from fastapi import APIRouter, Response
from prepza_common.limits.limits import limit

from assistant.constants.key_tools import KEY_TOOLS
from assistant.constants.mcp import TOOLS_CACHE_SECONDS
from assistant.integrations.redis import get_redis
from assistant.schemas.mcp import McpLimitsOut, McpToolOut, McpToolsOut
from assistant.services import mcp_tools

router = APIRouter(tags=["mcp"])


@router.get("/mcp/tools")
async def list_mcp_tools(response: Response) -> McpToolsOut:
    """The developer docs' MCP tab: the tools the MCP server lists, with their hints and the API
    key permission each needs, and the limits an AI app meets. Public, no user data."""
    response.headers["Cache-Control"] = f"public, max-age={TOOLS_CACHE_SECONDS}"
    tools = [
        McpToolOut(
            name=tool.name,
            description=tool.description or "",
            read_only=bool(tool.annotations.read_only_hint),
            destructive=bool(tool.annotations.destructive_hint),
            idempotent=bool(tool.annotations.idempotent_hint),
            key_permission=KEY_TOOLS.get(tool.name),
        )
        for tool in mcp_tools.listed()
    ]
    redis = get_redis()
    limits = McpLimitsOut(
        calls_per_minute=await limit(redis, "MCP_CALLS_PER_USER_MINUTE"),
        calls_per_day=await limit(redis, "MCP_CALLS_PER_USER_DAY"),
        writes_per_hour=await limit(redis, "ACTIONS_PER_USER_HOUR"),
    )

    return McpToolsOut(tools=tools, limits=limits)
