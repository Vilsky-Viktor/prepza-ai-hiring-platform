import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class OAuthClient(Base):
    """An AI app that registered itself (OAuth dynamic client registration) or named itself by its
    Client ID Metadata Document (its HTTPS address is the client_id), as it described itself: its
    name and the addresses it returns to. A document's copy is read again once older than
    METADATA_DOCUMENT_SECONDS (created_at: when it was read). Deleted once it has had no
    connection for IDLE_CLIENT_DAYS."""

    __tablename__ = "oauth_clients"

    client_id: Mapped[str] = mapped_column(Text(), primary_key=True)
    # The MCP SDK's OAuthClientInformationFull, as JSON.
    info: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class McpGrant(Base):
    """One connection: a user allowed an app to use prepza as them. Its tokens are kept as their
    hashes only; deleting the row disconnects the app."""

    __tablename__ = "mcp_grants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    client_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("oauth_clients.client_id", ondelete="CASCADE"), index=True
    )
    # What the user saw when they allowed it: the app's name and the site it returns to.
    client_name: Mapped[str] = mapped_column(String(80))
    redirect_host: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_hash: Mapped[str] = mapped_column(String(64), unique=True)
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # Refreshing moves it on: a connection in use doesn't expire.
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # The refresh token the last refresh replaced, and when: used again well after that, it was
    # likely stolen, and the connection goes (services/oauth_provider.py load_refresh_token).
    previous_refresh_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # What the user allowed: MCP_SCOPE (everything) or MCP_READ_SCOPE (only reading).
    scope: Mapped[str] = mapped_column(String(32), server_default="prepza")
