from uuid import UUID

from pydantic import BaseModel, Field

from api.constants.permissions import Permission


class KeyVerifyIn(BaseModel):
    # The whole key, as an AI agent sent it to the MCP server.
    key: str = Field(max_length=200)


class VerifiedKeyOut(BaseModel):
    """A working key: its company, the member it acts as, and what it may do."""

    id: UUID
    company_id: UUID
    created_by: str
    permissions: list[Permission]
