from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp_types as types
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import ProviderTokenVerifier
from mcp.server.auth.routes import build_resource_metadata_url
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from app.constants.mcp import MCP_PATH, MCP_REQUEST_HEADERS, MCP_SCOPE
from app.helpers.oauth import auth_settings
from app.prompts.mcp import MCP_INSTRUCTIONS
from app.services import mcp_tools
from app.services.oauth_provider import Provider


async def list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=mcp_tools.listed(ctx.request.user.access_token))


async def call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    # The connection the bearer token belongs to, checked before the request got here.
    access = ctx.request.user.access_token

    return await mcp_tools.call(params.name, params.arguments or {}, access)


server = Server(
    "prepza", instructions=MCP_INSTRUCTIONS, on_list_tools=list_tools, on_call_tool=call_tool
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
    401 naming where to learn how to get one. Browser-based apps (MCP Inspector) may call it."""
    resource = auth_settings().resource_server_url
    verifier = ProviderTokenVerifier(Provider())
    required = RequireAuthMiddleware(handle, [MCP_SCOPE], build_resource_metadata_url(resource))
    authenticated = AuthenticationMiddleware(
        required, backend=BearerAuthBackend(verifier, resource_server_url=resource)
    )
    endpoint = CORSMiddleware(
        authenticated,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=MCP_REQUEST_HEADERS,
        expose_headers=["WWW-Authenticate", "Mcp-Session-Id"],
    )

    return [Route(MCP_PATH, endpoint=endpoint)]
