import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, false, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class ApiKey(Base):
    """A company's API key, kept only as its SHA-256 hash; `shown` is its first characters."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    name: Mapped[str] = mapped_column(String(80))
    shown: Mapped[str] = mapped_column(String(20))
    hash: Mapped[str] = mapped_column(String(64), unique=True)
    # The owner or admin who made it: the API acts as them (their email limits), while they
    # still are one.
    created_by: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    # None: it never expires.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # What it may do (constants/permissions.py): only ever narrowed after it's made.
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String(32)))


class Webhook(Base):
    """An address that hears a company's events, signed with its own secret (encrypted)."""

    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    # An event it didn't take for RETRY_GIVE_UP was dropped; it took none since.
    failing: Mapped[bool] = mapped_column(default=False, server_default=false())
    # An event found the member who added it no longer an owner or admin: the company was told,
    # once. Cleared when its member is an editor again.
    stopped: Mapped[bool] = mapped_column(default=False, server_default=false())


class WebhookDelivery(Base):
    """An event a web hook got: a redelivered event isn't sent to it again."""

    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("webhooks.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class WebhookRetry(Base):
    """An event a web hook didn't take: the retry job sends it again, with backoff."""

    __tablename__ = "webhook_retries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("webhooks.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    # What the web hook gets, the same each time (the signature is made at sending).
    body: Mapped[str] = mapped_column(Text)
    # Sends that failed so far.
    attempts: Mapped[int]
    next_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class WebhookAttempt(Base):
    """A send to a web hook and how it went, for its delivery log on the API page: the latest
    WEBHOOK_LOG_KEPT per web hook. No candidate's data, only the event's id and type."""

    __tablename__ = "webhook_attempts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    webhook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("webhooks.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(64))
    # Whether it took it, and what happened: "delivered", the status it answered, the error, or
    # why it was skipped.
    ok: Mapped[bool]
    result: Mapped[str] = mapped_column(String(64))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
