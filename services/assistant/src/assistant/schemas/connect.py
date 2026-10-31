from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConnectRequestOut(BaseModel):
    """An AI app's request to connect, as the consent page shows it."""

    client_name: str
    redirect_host: str
    # False: testee doesn't know the site the app returns to, and the page warns about it.
    known_client: bool
    # The app asked only to read: the page offers no choice.
    read_only: bool


class ApproveIn(BaseModel):
    """The user's choice: let the app only read (an app that asked for more)."""

    read_only: bool = False


class RedirectOut(BaseModel):
    """Where the browser goes next: back to the app."""

    redirect_url: str


class ConnectionOut(BaseModel):
    """One of the user's connected AI apps."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_name: str
    redirect_host: str
    created_at: datetime
    last_used_at: datetime | None
    # What the user allowed: MCP_SCOPE (everything) or MCP_READ_SCOPE (only reading).
    scope: str
