from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp_types as types
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import ProviderTokenVerifier
from mcp.server.auth.routes import build_resource_metadata_url
from mcp.server.caching import CacheHint
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from assistant.constants.mcp import CACHE_TTL_MS, MCP_PATH, MCP_READ_SCOPE, MCP_REQUEST_HEADERS
from assistant.helpers.cors import browser_cors
from assistant.helpers.oauth import auth_settings
from assistant.prompts.mcp import MCP_INSTRUCTIONS
from assistant.services import mcp_tools
from assistant.services.oauth_provider import Provider


async def list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=mcp_tools.listed(ctx.request.user.access_token))


async def call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    # The connection the bearer token belongs to, checked before the request got here.
    access = ctx.request.user.access_token

    return await mcp_tools.call(params.name, params.arguments or {}, access)


# How long an app may reuse the tools and the server's description (2026-07-28). The tools vary
# by caller (an API key's permissions, a read-only connection), so their cache is private; the
# description is the same for everyone.
CACHE_HINTS = {
    "tools/list": CacheHint(ttl_ms=CACHE_TTL_MS, scope="private"),
    "server/discover": CacheHint(ttl_ms=CACHE_TTL_MS, scope="public"),
}
server = Server(
    "prepza",
    instructions=MCP_INSTRUCTIONS,
    on_list_tools=list_tools,
    on_call_tool=call_tool,
    cache_hints=CACHE_HINTS,
)
# Stateless, with plain JSON answers: any instance answers any request, with no sessions to keep
# and no streams held open. A manager runs once, so each start of the app makes its own.
manager: StreamableHTTPSessionManager | None = None


@asynccontextmanager
async def running() -> AsyncIterator[None]:
    global manager
    manager = StreamableHTTPSessionManager(app=server, stateless=True, json_response=True)

    async with manager.run():
        yield


async def handle(scope: Scope, receive: Receive, send: Send) -> None:
    await manager.handle_request(scope, receive, send)


def routes() -> list[Route]:
    """The MCP endpoint, for the bearer of an access token prepza issued for it; without one, a
    401 naming where to learn how to get one. Browser-based apps we know (MCP Inspector) may call
    it."""
    resource = auth_settings().resource_server_url
    verifier = ProviderTokenVerifier(Provider())
    required = RequireAuthMiddleware(
        handle, [MCP_READ_SCOPE], build_resource_metadata_url(resource)
    )
    authenticated = AuthenticationMiddleware(
        required, backend=BearerAuthBackend(verifier, resource_server_url=resource)
    )
    endpoint = browser_cors(
        authenticated,
        ["GET", "POST", "DELETE", "OPTIONS"],
        MCP_REQUEST_HEADERS,
        expose=["WWW-Authenticate", "Mcp-Session-Id"],
    )

    return [Route(MCP_PATH, endpoint=endpoint)]
