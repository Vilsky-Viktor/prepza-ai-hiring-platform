import logging
from uuid import UUID

from testee_common.events.deletions import USER_DELETED

from assistant.constants.events import (
    CANDIDATE_INTERVIEW_DELETED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
)
from assistant.handlers import (
    candidate_interview_deleted,
    candidate_removed,
    company_deleted,
    user_deleted,
)

logger = logging.getLogger(__name__)

# Each event the assistant acts on, to its handler; each returns how many conversations went.
HANDLERS = {
    COMPANY_DELETED: company_deleted.handle,
    CANDIDATE_REMOVED: candidate_removed.handle,
    CANDIDATE_INTERVIEW_DELETED: candidate_interview_deleted.handle,
}


async def handle(event_type: str, data: dict) -> None:
    """Companies' events, each to its handler, with the company it's about, and accounts'
    `user.deleted`. Safe on a redelivery: nothing is left to delete. Other events are ignored."""
    if event_type == USER_DELETED:
        await user_deleted.handle(data)

        return

    handler = HANDLERS.get(event_type)

    if handler is None:
        return

    # A malformed id raises ValueError: no retry can fix it, so the event is dropped
    # (testee_common.events.unhandleable).
    deleted = await handler(UUID(str(data.get("company_id"))), data)

    if deleted:
        logger.info("Deleted %d assistant conversations (%s)", deleted, event_type)
