from prepza_common.events import outbox

from rounds.constants.events import CONTACT_SENT
from rounds.core.db import Session
from rounds.models.outbox import OutboxEvent


async def save(data: dict) -> None:
    """Keeps the message as an event until it's published; notifications emails it."""
    async with Session() as session:
        outbox.add(session, OutboxEvent, CONTACT_SENT, data)
        await session.commit()
