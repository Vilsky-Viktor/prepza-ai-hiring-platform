from datetime import UTC, datetime, timedelta

from mcp.server.auth.settings import AuthSettings
from mcp.shared.auth import OAuthToken
from prepza_common.auth.tokens import new_token

from app.config.settings import settings
from app.constants.mcp import (
    ACCESS_SECONDS,
    FUNNEL_CLIENTS,
    MCP_PATH,
    MCP_READ_SCOPE,
    MCP_SCOPE,
    REFRESH_SECONDS,
    TOKEN_BYTES,
    TOKEN_PREFIX,
)


def resource_url() -> str:
    """The MCP endpoint, the one resource prepza's access is for."""
    return settings.site_url.rstrip("/") + MCP_PATH


def other_resource(resource: str | None) -> bool:
    """A request naming a resource other than the MCP endpoint (RFC 8707); one naming none is
    for the MCP endpoint, the only one."""
    return resource is not None and resource.rstrip("/") != resource_url()


def auth_settings() -> AuthSettings:
    """The site as the authorization server (its root is the issuer) and the MCP endpoint as
    the resource, as URLs the SDK writes without a trailing slash."""
    return AuthSettings(
        issuer_url=settings.site_url.rstrip("/"),
        resource_server_url=resource_url(),
        validate_token_resource=True,
    )


def funnel_client(client_name: str) -> str:
    return FUNNEL_CLIENTS.get(client_name, "other")


def scopes_of(scope: str) -> list[str]:
    """What a connection's scope lets it do: the full scope includes reading."""
    return [MCP_SCOPE, MCP_READ_SCOPE] if scope == MCP_SCOPE else [MCP_READ_SCOPE]


def granted_scope(asked: list[str], read_only: bool) -> str:
    """The scope a connection gets: read only when the app asked for nothing more, or the user
    chose it on the consent page."""
    return MCP_SCOPE if MCP_SCOPE in asked and not read_only else MCP_READ_SCOPE


def new_tokens(scope: str = MCP_SCOPE) -> tuple[OAuthToken, dict]:
    """A new access and refresh token for the app, and what the connection keeps of them."""
    access, access_hash = new_token(TOKEN_PREFIX, TOKEN_BYTES)
    refresh, refresh_hash = new_token(TOKEN_PREFIX, TOKEN_BYTES)
    now = datetime.now(UTC)
    kept = {
        "access_hash": access_hash,
        "access_expires_at": now + timedelta(seconds=ACCESS_SECONDS),
        "refresh_hash": refresh_hash,
        "refresh_expires_at": now + timedelta(seconds=REFRESH_SECONDS),
    }
    token = OAuthToken(
        access_token=access, expires_in=ACCESS_SECONDS, scope=scope, refresh_token=refresh
    )

    return token, kept
