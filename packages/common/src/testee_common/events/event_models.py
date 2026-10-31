# The columns of the tables every service with events keeps alike; each service's model adds its
# table name to one of these and its own Base.
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


def now() -> datetime:
    return datetime.now(UTC)


class OutboxColumns:
    """An event saved with the change it announces, until it's published (testee_common.events.outbox)."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    # Times Pub/Sub refused it; parked past OUTBOX_MAX_ATTEMPTS.
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    # The trace header of the request that saved it, sent with it (pubsub.TRACE_ATTRIBUTE).
    trace: Mapped[str | None] = mapped_column(String(256))


class ProcessedEventColumns:
    """An event already handled; Pub/Sub may deliver it again (testee_common.events.processed_events)."""

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
