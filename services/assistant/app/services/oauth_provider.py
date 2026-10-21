import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from mcp.server.auth.provider import (
    AuthorizationParams,
    AuthorizeError,
    RegistrationError,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from prepza_common.analytics import track
from prepza_common.tokens import hashed

from app.config.settings import settings
from app.constants.limits import MAX_REGISTRATION_BYTES, MAX_STATE_LENGTH
from app.constants.mcp import (
    API_KEY_PREFIX,
    CONNECT_PATH,
    MCP_SCOPE,
    REFRESH_REUSE_GRACE_SECONDS,
)
from app.helpers.mcp_clients import describe_client, is_document_id, refused_redirect
from app.helpers.oauth import funnel_client, new_tokens, resource_url, scopes_of
from app.models.oauth import McpGrant
from app.models.oauth_tokens import Access, Client, Code, Refresh
from app.services import client_documents
from app.services.mcp_keys import key_access
from app.services.oauth_limits import limit_tokens
from app.storage import oauth, oauth_requests

logger = logging.getLogger(__name__)


async def revoke_if_replayed(refresh_hash: str) -> None:
    """A refresh token a refresh replaced, used again: within REFRESH_REUSE_GRACE_SECONDS, an app
    that refreshed twice at once (just refused); later, likely a stolen copy, so the connection
    goes and the app asks the user again (OAuth 2.1)."""
    grant = await oauth.by_previous_refresh(refresh_hash)

    if grant is None or grant.refreshed_at is None:
        return

    grace = timedelta(seconds=REFRESH_REUSE_GRACE_SECONDS)

    if datetime.now(UTC) - grant.refreshed_at > grace:
        logger.warning("A replaced refresh token was used again: connection %s revoked", grant.id)
        await oauth.remove(grant.id)


class Provider:
    """prepza as the authorization server of AI apps (the MCP SDK's
    OAuthAuthorizationServerProvider): apps register themselves, the user allows them on the
    site's /connect page, and they get opaque tokens, kept as hashes, one connection each."""

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """An app that registered, or one named by its metadata document's address."""
        if is_document_id(client_id):
            found = await client_documents.client_of(client_id)
        else:
            found = await oauth.get_client(client_id)

        return Client.model_validate(found) if found else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Kept 30 days; one bigger than MAX_REGISTRATION_BYTES is refused."""
        info = client_info.model_dump(mode="json", exclude_none=True)

        if len(json.dumps(info)) > MAX_REGISTRATION_BYTES:
            raise RegistrationError("invalid_client_metadata", "The registration is too large.")

        if any(refused_redirect(str(uri)) for uri in client_info.redirect_uris or []):
            raise RegistrationError("invalid_redirect_uri", "Return addresses must open an app.")

        await oauth.save_client(client_info.client_id, info)

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Keeps the request for the user to answer, and sends them to the consent page."""
        if params.resource is not None and params.resource.rstrip("/") != resource_url():
            raise AuthorizeError("invalid_target", "prepza only grants access to its MCP server.")

        # Kept with the request until the user answers.
        if params.state is not None and len(params.state) > MAX_STATE_LENGTH:
            raise AuthorizeError("invalid_request", "The state is too long.")

        name, host, known = describe_client(client.client_name, str(params.redirect_uri))
        request_id = secrets.token_urlsafe(24)
        request = {
            "client_id": client.client_id,
            "client_name": name,
            "redirect_host": host,
            "known_client": known,
            "redirect_uri": str(params.redirect_uri),
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "code_challenge": params.code_challenge,
            "state": params.state,
            "scopes": params.scopes or [MCP_SCOPE],
        }
        await oauth_requests.save_request(request_id, request)

        return f"{settings.site_url.rstrip('/')}{CONNECT_PATH}?request={request_id}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> Code | None:
        found = await oauth_requests.peek_code(hashed(authorization_code))

        if found is None or found["client_id"] != client.client_id:
            return None

        return Code(
            code=authorization_code,
            scopes=found["scopes"],
            expires_at=found["expires_at"],
            client_id=found["client_id"],
            code_challenge=found["code_challenge"],
            redirect_uri=found["redirect_uri"],
            redirect_uri_provided_explicitly=found["redirect_uri_provided_explicitly"],
            resource=resource_url(),
            subject=found["user_id"],
            client_name=found["client_name"],
            redirect_host=found["redirect_host"],
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: Code
    ) -> OAuthToken:
        """The code, once, for the connection's first tokens."""
        await limit_tokens(client.client_id)

        if await oauth_requests.take_code(hashed(authorization_code.code)) is None:
            raise TokenError("invalid_grant", "authorization code does not exist")

        scope = authorization_code.scopes[0]
        token, kept = new_tokens(scope)
        grant = McpGrant(
            scope=scope,
            user_id=authorization_code.subject,
            client_id=client.client_id,
            client_name=authorization_code.client_name,
            redirect_host=authorization_code.redirect_host,
            **kept,
        )
        await oauth.add_grant(grant)
        client_label = funnel_client(authorization_code.client_name)
        await track("mcp_connected", user_id=authorization_code.subject, client=client_label)

        return token

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> Refresh | None:
        grant = await oauth.by_refresh(hashed(refresh_token))

        if grant is None:
            await revoke_if_replayed(hashed(refresh_token))

            return None

        if grant.client_id != client.client_id:
            return None

        return Refresh(
            token=refresh_token,
            client_id=grant.client_id,
            scopes=scopes_of(grant.scope),
            expires_at=int(grant.refresh_expires_at.timestamp()),
            resource=resource_url(),
            subject=grant.user_id,
            grant_id=str(grant.id),
        )

    async def exchange_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: Refresh, scopes: list[str]
    ) -> OAuthToken:
        """New tokens for the connection; the old ones stop working. Of two refreshes with the
        same token, the second is refused."""
        await limit_tokens(client.client_id)
        scope = MCP_SCOPE if MCP_SCOPE in refresh_token.scopes else refresh_token.scopes[0]
        token, kept = new_tokens(scope)

        if not await oauth.rotate(UUID(refresh_token.grant_id), hashed(refresh_token.token), kept):
            raise TokenError("invalid_grant", "refresh token does not exist")

        return token

    async def load_access_token(self, token: str) -> Access | None:
        """An app's access token, or an AI agent's company API key."""
        if token.startswith(API_KEY_PREFIX):
            return await key_access(token)

        grant = await oauth.by_access(hashed(token))

        if grant is None or grant.access_expires_at <= datetime.now(UTC):
            return None

        return Access(
            token=token,
            client_id=grant.client_id,
            scopes=scopes_of(grant.scope),
            expires_at=int(grant.access_expires_at.timestamp()),
            resource=resource_url(),
            subject=grant.user_id,
            grant_id=str(grant.id),
            client_name=grant.client_name,
        )

    async def revoke_token(self, token: Access | Refresh) -> None:
        """The app disconnects itself (it was removed there): the connection goes. An API key
        is deleted in prepza only."""
        if token.grant_id is None:
            return

        removed = await oauth.remove(UUID(token.grant_id))

        if removed is not None:
            await track("mcp_disconnected", user_id=removed.user_id, by="client")
