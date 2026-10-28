from mcp.server.auth.provider import AccessToken, AuthorizationCode, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl, Field

from assistant.helpers.mcp_clients import same_loopback


class Code(AuthorizationCode):
    """A code the user's allowing gave the app, with what the connection is called."""

    client_name: str
    redirect_host: str


class Refresh(RefreshToken):
    grant_id: str


class Access(AccessToken):
    """An app's access (its connection, grant_id), or an AI agent's API key: the key's id, its
    company and permissions."""

    client_name: str
    grant_id: str | None = None
    key_id: str | None = None
    company_id: str | None = None
    permissions: list[str] = Field(default_factory=list)


class Client(OAuthClientInformationFull):
    """An AI app as the MCP SDK checks it, whose return address on the user's own computer may
    be on any port (helpers/mcp_clients.py same_loopback)."""

    def validate_redirect_uri(self, redirect_uri: AnyUrl | None) -> AnyUrl:
        registered = [str(uri) for uri in self.redirect_uris or []]

        if redirect_uri is not None and same_loopback(registered, str(redirect_uri)):
            return redirect_uri

        return super().validate_redirect_uri(redirect_uri)
