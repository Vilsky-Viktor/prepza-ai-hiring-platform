# The bell's notifications as they're kept: stored once each (a grouped kind adding to a recent
# one), marked seen, and removed with what a deletion takes.
from datetime import UTC, datetime

from notifications.constants.notifications import GROUPED_KINDS
from notifications.core.db import Session
from notifications.repositories import notifications


async def store(key: str, event: dict) -> bool:
    """Stores a requested notification once per `key` (the event's id, or the producer's
    `key`), however often it comes; False when it was already there. A deleted company gets
    none, even from an event that was on its way. A grouped kind adds to a recent one about the
    same thing instead. Then the recipient's oldest go, beyond MAX_PER_RECIPIENT or KEEP_DAYS.
    All of it is one save."""
    now = datetime.now(UTC)
    recipient = f"{event['recipient']}:{event['recipient_id']}"

    async with Session.begin() as session:
        await notifications.lock_recipient(session, recipient)

        if await notifications.is_deleted(session, recipient):
            return False

        if not await notifications.claim(session, key, now):
            return False

        grouped = event["kind"] in GROUPED_KINDS and await notifications.add_to_group(
            session, event, now
        )

        if not grouped:
            await notifications.add(session, key, event, now)

        await notifications.prune(session, event, now)

    return True


async def mark_seen(user_id: str) -> None:
    """Opening the bell: everything so far counts as read."""
    async with Session.begin() as session:
        await notifications.mark_seen(session, user_id, datetime.now(UTC))


async def remove_candidate(email: str, company_id: str) -> None:
    """A company erased a candidate: its notifications about them go. Safe to repeat."""
    async with Session.begin() as session:
        await notifications.remove_candidate(session, email, company_id)


async def remove_interview_candidates(company_id: str, interview_id: str) -> None:
    """A company deleted an interview, its candidates with it: its notifications about them go.
    Safe to repeat."""
    async with Session.begin() as session:
        await notifications.remove_interview_candidates(session, company_id, interview_id)


async def remove_news(news_id: str) -> None:
    """A deleted news post's notification for everyone goes. Safe to repeat."""
    async with Session.begin() as session:
        await notifications.remove_news(session, news_id)
