from prepza_common.events import outbox

from app.constants.events import CONTACT_SENT
from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def save(data: dict) -> None:
    """Keeps the message as an event until it's published; notifications emails it."""
    async with Session() as session:
        outbox.add(session, OutboxEvent, CONTACT_SENT, data)
        await session.commit()
