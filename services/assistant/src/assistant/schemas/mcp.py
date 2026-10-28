from pydantic import BaseModel


class McpToolOut(BaseModel):
    name: str
    description: str
    # Whether it only reads; a write that can't be undone; one that leaves the same result when
    # repeated (the hints apps see).
    read_only: bool
    destructive: bool
    idempotent: bool
    # The API key permission it needs at the MCP server ("mcp": nothing more); None: keys don't
    # get it, only AI apps signed in as a person.
    key_permission: str | None


class McpLimitsOut(BaseModel):
    calls_per_minute: int
    calls_per_day: int
    writes_per_hour: int


class McpToolsOut(BaseModel):
    tools: list[McpToolOut]
    limits: McpLimitsOut
