from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events import outbox

from generation.models.outbox import OutboxEvent


def add(session: AsyncSession, event: tuple[str, dict]) -> None:
    """An event saved with the change it tells of, for the outbox to publish once committed."""
    outbox.add(session, OutboxEvent, *event)
