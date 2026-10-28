from datetime import UTC, datetime, timedelta

from companies.constants.invites import REMINDER_AFTER_DAYS
from companies.repositories import reminders
from companies.services import outbox as outbox_service


async def remind_unstarted() -> int:
    """Reminds candidates who haven't started REMINDER_AFTER_DAYS after their invite, once."""
    count = await reminders.remind_unstarted(
        datetime.now(UTC) - timedelta(days=REMINDER_AFTER_DAYS)
    )
    await outbox_service.flush_quietly()

    return count
