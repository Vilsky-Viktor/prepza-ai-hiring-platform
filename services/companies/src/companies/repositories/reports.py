from prepza_common.events import outbox

from companies.constants.events import REPORT_SHARED
from companies.core.db import Session
from companies.models.outbox import OutboxEvent


async def queue_email(data: dict) -> None:
    """Saves the report.shared event; the outbox publishes it and notifications sends it."""
    async with Session() as session:
        outbox.add(session, OutboxEvent, REPORT_SHARED, data)
        await session.commit()
