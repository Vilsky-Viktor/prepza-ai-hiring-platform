from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import REPORT_SHARED
from companies.repositories import outbox


async def queue_email(session: AsyncSession, data: dict) -> None:
    """Saves the report.shared event; the outbox publishes it and notifications sends it."""
    outbox.add(session, REPORT_SHARED, data)
