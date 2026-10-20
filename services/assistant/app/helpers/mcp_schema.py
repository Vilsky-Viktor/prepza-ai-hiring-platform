import mcp_types as types

from app.constants.mcp_descriptions import MCP_DESCRIPTIONS
from app.constants.mcp_titles import MCP_TITLES
from app.models.tools import Tool

# Writes that leave the same result when repeated.
IDEMPOTENT_METHODS = ("PUT", "DELETE")


def mcp_tool(tool: Tool) -> types.Tool:
    """A registry tool as an AI app sees it: its function definition's name, description (a
    fuller one for an app where the panel's is short) and parameters, the title the app shows, and all four hints for the app's own approval prompt
    (a read, a write, one that can't be undone, one safe to repeat), never left to their
    defaults (destructive, open world). Every tool works on prepza alone, never the open web."""
    function = tool.definition["function"]
    read_only = tool.method == "GET"
    annotations = types.ToolAnnotations(
        read_only_hint=read_only,
        destructive_hint=not read_only and tool.destructive,
        idempotent_hint=read_only or tool.method in IDEMPOTENT_METHODS,
        open_world_hint=False,
    )

    return types.Tool(
        name=tool.name,
        title=MCP_TITLES.get(tool.name),
        description=MCP_DESCRIPTIONS.get(tool.name, function["description"]),
        input_schema=function["parameters"],
        annotations=annotations,
    )
