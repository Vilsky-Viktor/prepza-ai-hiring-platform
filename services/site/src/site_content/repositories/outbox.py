from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events import outbox
from testee_common.events.notifications import NOTIFICATION_REQUESTED

from site_content.constants.events import CONTACT_SENT
from site_content.models.outbox import OutboxEvent


def add(session: AsyncSession, event_type: str, data: dict) -> None:
    """Keeps the event with the transaction's change, until it's published."""
    outbox.add(session, OutboxEvent, event_type, data)


def notify(session: AsyncSession, notice: dict) -> None:
    """A notification for notifications to deliver, saved in `session` with its change."""
    add(session, NOTIFICATION_REQUESTED, notice)


def from_sender(email: str):
    """Contact messages sent from `email` (any case), still here: waiting to be published or
    within the days published events are kept (OUTBOX_KEEP_DAYS)."""
    return (OutboxEvent.event_type == CONTACT_SENT) & (
        func.lower(OutboxEvent.data["email"].astext) == email.lower()
    )


async def contact_messages(session: AsyncSession, email: str) -> list[OutboxEvent]:
    found = await session.scalars(
        select(OutboxEvent).where(from_sender(email)).order_by(OutboxEvent.created_at)
    )

    return list(found)


async def delete_contact_messages(session: AsyncSession, email: str) -> None:
    await session.execute(delete(OutboxEvent).where(from_sender(email)))
