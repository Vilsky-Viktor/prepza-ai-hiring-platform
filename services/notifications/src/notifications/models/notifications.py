import uuid
from datetime import UTC, datetime

from prepza_common.db.db import one_of
from prepza_common.events.notifications import NotificationKind, Recipient
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from notifications.models.base import Base


class Notification(Base):
    """One notification for a user, or for every member of a company (see
    prepza_common.events.notifications)."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient", "recipient", "recipient_id", "created_at"),
        # The notifications about a person, found by their email when they're erased.
        Index("ix_notifications_email", text("(data ->> 'email')")),
        CheckConstraint(one_of("recipient", Recipient), name="ck_notifications_recipient"),
        CheckConstraint(one_of("kind", NotificationKind), name="ck_notifications_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # The event's id (pubsub.event_of): a retried or re-sent event is stored once.
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    recipient: Mapped[str] = mapped_column(String(16))
    recipient_id: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(64))
    link: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )


class Seen(Base):
    """When a user last opened the bell: what came after counts as unread. Per user, so one
    company admin reading the company's notifications doesn't read them for the others."""

    __tablename__ = "seen"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Received(Base):
    """Every event that asked for a notification, so a retried one is stored once even when it
    was added to a group."""

    __tablename__ = "received"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
