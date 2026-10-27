from prepza_common.events import outbox

from app.constants.events import REPORT_SHARED
from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def queue_email(data: dict) -> None:
    """Saves the report.shared event; the outbox publishes it and notifications sends it."""
    async with Session() as session:
        outbox.add(session, OutboxEvent, REPORT_SHARED, data)
        await session.commit()
