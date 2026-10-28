from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy.ext.asyncio import AsyncSession

from billing.models.outbox import OutboxEvent


def save(session: AsyncSession, events: list[tuple[str, dict]]) -> None:
    """Saves `events` (type, data) in the caller's transaction, to be published by the outbox."""
    for event_type, data in events:
        outbox.add(session, OutboxEvent, event_type, data)


def tell(session: AsyncSession, notice: dict) -> None:
    """A notification for the bell, kept in the outbox in the caller's transaction: retried until
    Pub/Sub takes it, where a direct publish would lose it."""
    outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)
