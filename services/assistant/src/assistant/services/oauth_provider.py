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
from prepza_common.auth.tokens import hashed
from prepza_common.events.analytics import track

from assistant.config import settings
from assistant.constants.limits import MAX_REGISTRATION_BYTES, MAX_STATE_LENGTH
from assistant.constants.mcp import (
    API_KEY_PREFIX,
    CONNECT_PATH,
    MCP_SCOPE,
    OTHER_RESOURCE,
    REFRESH_REUSE_GRACE_SECONDS,
)
from assistant.core.db import Session
from assistant.helpers.mcp_clients import describe_client, is_document_id, refused_redirect
from assistant.helpers.oauth import (
    funnel_client,
    new_tokens,
    other_resource,
    resource_url,
    scopes_of,
)
from assistant.models.oauth import McpGrant
from assistant.models.oauth_tokens import Access, Client, Code, Refresh
from assistant.repositories import oauth, oauth_requests
from assistant.services import client_documents
from assistant.services.mcp_keys import key_access

logger = logging.getLogger(__name__)


async def revoke_if_replayed(refresh_hash: str) -> None:
    """A refresh token a refresh replaced, used again: within REFRESH_REUSE_GRACE_SECONDS, an app
    that refreshed twice at once (just refused); later, likely a stolen copy, so the connection
    goes and the app asks the user again (OAuth 2.1)."""
    grace = timedelta(seconds=REFRESH_REUSE_GRACE_SECONDS)

    async with Session.begin() as session:
        grant = await oauth.by_previous_refresh(session, refresh_hash)

        if grant is None or grant.refreshed_at is None:
            return

        if datetime.now(UTC) - grant.refreshed_at > grace:
            logger.warning(
                "A replaced refresh token was used again: connection %s revoked", grant.id
            )
            await oauth.remove(session, grant.id)


class Provider:
    """prepza as the authorization server of AI apps (the MCP SDK's
    OAuthAuthorizationServerProvider): apps register themselves, the user allows them on the
    site's /connect page, and they get opaque tokens, kept as hashes, one connection each."""

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """An app that registered, or one named by its metadata document's address."""
        if is_document_id(client_id):
            found = await client_documents.client_of(client_id)
        else:
            async with Session() as session:
                found = await oauth.get_client(session, client_id)

        return Client.model_validate(found) if found else None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Kept 30 days; one bigger than MAX_REGISTRATION_BYTES is refused."""
        info = client_info.model_dump(mode="json", exclude_none=True)

        if len(json.dumps(info)) > MAX_REGISTRATION_BYTES:
            raise RegistrationError("invalid_client_metadata", "The registration is too large.")

        if any(refused_redirect(str(uri)) for uri in client_info.redirect_uris or []):
            raise RegistrationError("invalid_redirect_uri", "Return addresses must open an app.")

        async with Session.begin() as session:
            await oauth.save_client(session, client_info.client_id, info)

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Keeps the request for the user to answer, and sends them to the consent page."""
        if other_resource(params.resource):
            raise AuthorizeError("invalid_target", OTHER_RESOURCE)

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

        async with Session.begin() as session:
            await oauth.add_grant(session, grant)

        client_label = funnel_client(authorization_code.client_name)
        await track("mcp_connected", user_id=authorization_code.subject, client=client_label)

        return token

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> Refresh | None:
        async with Session() as session:
            grant = await oauth.by_refresh(session, hashed(refresh_token))

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
        scope = MCP_SCOPE if MCP_SCOPE in refresh_token.scopes else refresh_token.scopes[0]
        token, kept = new_tokens(scope)

        grant_id = UUID(refresh_token.grant_id)

        async with Session.begin() as session:
            rotated = await oauth.rotate(session, grant_id, hashed(refresh_token.token), kept)

        if not rotated:
            raise TokenError("invalid_grant", "refresh token does not exist")

        return token

    async def load_access_token(self, token: str) -> Access | None:
        """An app's access token, or an AI agent's company API key."""
        if token.startswith(API_KEY_PREFIX):
            return await key_access(token)

        async with Session() as session:
            grant = await oauth.by_access(session, hashed(token))

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

        async with Session.begin() as session:
            removed = await oauth.remove(session, UUID(token.grant_id))

        if removed is not None:
            await track("mcp_disconnected", user_id=removed.user_id, by="client")
