import uuid
from datetime import UTC, datetime

from prepza_common.db import one_of
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.bulk import BulkKind, RecipientStatus
from app.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class BulkSend(Base):
    """One email to many users (constants/bulk.py BulkKind): a legal notice, about a document's
    version, or a campaign, about its id. Once each: (kind, about) is unique. Its recipients are
    worked out a page at a time, each run going on after the last id read (`prepared_after`),
    until the audience ends (`prepared_at`); it's finished when none is pending, or when it was
    stopped."""

    __tablename__ = "bulk_sends"
    __table_args__ = (
        UniqueConstraint("kind", "about"),
        CheckConstraint(one_of("kind", BulkKind), name="ck_bulk_sends_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(16))
    about: Mapped[str] = mapped_column(Text())
    asked_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    prepared_after: Mapped[str | None] = mapped_column(Text())
    prepared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BulkRecipient(Base):
    """One user a bulk send goes to, once: (send_id, user_id) is unique, and each row is claimed
    under a lock while it's sent (storage/bulk_recipients.py). `status` is a RecipientStatus,
    `reason` why it was skipped or failed. A spam complaint or an unsubscribe from the email is
    marked on it, for the campaign's counts."""

    __tablename__ = "bulk_recipients"
    __table_args__ = (
        UniqueConstraint("send_id", "user_id"),
        Index("ix_bulk_recipients_status", "status", "send_id"),
        CheckConstraint(one_of("status", RecipientStatus), name="ck_bulk_recipients_status"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    send_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bulk_sends.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(8), default="pending")
    reason: Mapped[str | None] = mapped_column(String(200))
    attempts: Mapped[int] = mapped_column(default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    complained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
