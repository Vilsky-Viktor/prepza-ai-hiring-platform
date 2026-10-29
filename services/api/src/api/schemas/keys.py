from uuid import UUID

from pydantic import BaseModel, Field

from api.constants.permissions import Permission


class KeyVerifyIn(BaseModel):
    # The whole key, as an AI agent sent it to the MCP server.
    key: str = Field(max_length=200)
    # The agent's IP address, as the assistant read it from its request; None from a caller
    # that doesn't send it, which a key limited to some addresses refuses.
    ip: str | None = Field(default=None, max_length=64)


class VerifiedKeyOut(BaseModel):
    """A working key: its company and what it may do. It acts as itself, never its maker."""

    id: UUID
    company_id: UUID
    permissions: list[Permission]
