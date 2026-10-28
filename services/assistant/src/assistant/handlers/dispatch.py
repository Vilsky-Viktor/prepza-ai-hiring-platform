import logging
from uuid import UUID

from assistant.constants.events import (
    CANDIDATE_INTERVIEW_DELETED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
)
from assistant.handlers import candidate_interview_deleted, candidate_removed, company_deleted

logger = logging.getLogger(__name__)

# Each event the assistant acts on, to its handler; each returns how many conversations went.
HANDLERS = {
    COMPANY_DELETED: company_deleted.handle,
    CANDIDATE_REMOVED: candidate_removed.handle,
    CANDIDATE_INTERVIEW_DELETED: candidate_interview_deleted.handle,
}


async def handle(event_type: str, data: dict) -> None:
    """Companies' events, each to its handler, with the company it's about. Safe on a
    redelivery: nothing is left to delete. Other events are ignored."""
    handler = HANDLERS.get(event_type)

    if handler is None:
        return

    try:
        company_id = UUID(str(data.get("company_id")))
    except ValueError:
        # Retrying can't fix it: dropped, so Pub/Sub doesn't send it again and again.
        logger.warning("Dropped %s for a malformed company %r", event_type, data.get("company_id"))

        return

    deleted = await handler(company_id, data)

    if deleted:
        logger.info("Deleted %d assistant conversations (%s)", deleted, event_type)
