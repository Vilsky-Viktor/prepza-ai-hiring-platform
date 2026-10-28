from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.outbox import OutboxEvent


def add(session: AsyncSession, event_type: str, data: dict) -> None:
    """An event saved in `session`, with the change it tells of; published once committed."""
    outbox.add(session, OutboxEvent, event_type, data)


def notify(session: AsyncSession, notice: dict) -> None:
    """A notification for notifications to deliver, saved in `session` with its change."""
    add(session, NOTIFICATION_REQUESTED, notice)
