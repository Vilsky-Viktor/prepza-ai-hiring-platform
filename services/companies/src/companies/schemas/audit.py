from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditEventOut(BaseModel):
    user_id: str
    action: str
    target_id: UUID | None
    # "assistant" when the in-app assistant read for the user, "mcp" when an AI app they
    # connected (or an AI agent with an API key) did, "api" for an API key; None for the app
    # itself.
    via: str | None = None
    # The API key that took it, itself and never a person (over the API or MCP); None otherwise.
    key_id: UUID | None = None
    created_at: datetime


class ActionOut(AuditEventOut):
    """A row of a company's action log (its owner's tab, the admin zone's support page): its
    group, who took it (`user_email`, None once they're no longer a member), and what it was
    about: `target_kind` and `target` (a candidate's or member's email, an interview's title, an
    API key's name, a web hook's host, an integration's name; None for the company itself, or a
    person who's gone), and what it took away (`removed`: an API key's permissions). An API key
    that took it is named by `key_name`, its name now (None once it was deleted), instead of a
    member."""

    id: UUID
    group: str | None
    user_email: str | None
    target_kind: str | None
    target: str | None
    removed: list[str] | None = None
    key_name: str | None = None
