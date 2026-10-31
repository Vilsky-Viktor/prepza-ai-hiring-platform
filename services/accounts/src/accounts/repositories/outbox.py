from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events import outbox

from accounts.models.outbox import OutboxEvent


def add(session: AsyncSession, event_type: str, data: dict) -> None:
    """Keeps the event with the transaction's change, until it's published."""
    outbox.add(session, OutboxEvent, event_type, data)
