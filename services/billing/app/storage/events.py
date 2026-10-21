from prepza_common import outbox
from prepza_common.notifications import NOTIFICATION_REQUESTED

from app.models.outbox import OutboxEvent
from app.storage.db import Session


def save(session, events: list[tuple[str, dict]]) -> None:
    """Saves `events` (type, data) in the caller's transaction, to be published by the outbox."""
    for event_type, data in events:
        outbox.add(session, OutboxEvent, event_type, data)


async def tell(notice: dict) -> None:
    """A notification for the bell, kept in the outbox in a transaction of its own: retried until
    Pub/Sub takes it, where a direct publish would lose it."""
    async with Session() as session:
        outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)
        await session.commit()
