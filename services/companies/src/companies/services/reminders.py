from datetime import UTC, datetime, timedelta

from companies.constants.invites import REMINDER_AFTER_DAYS
from companies.core.db import Session
from companies.repositories import reminders
from companies.services import outbox as outbox_service


async def remind_unstarted() -> int:
    """Reminds candidates who haven't started REMINDER_AFTER_DAYS after their invite, once: each
    reminder is saved with the invite marked reminded."""
    async with Session.begin() as session:
        count = await reminders.remind_unstarted(
            session, datetime.now(UTC) - timedelta(days=REMINDER_AFTER_DAYS)
        )

    await outbox_service.flush_quietly()

    return count
