import logging
from uuid import UUID

from app.constants.events import CANDIDATE_INTERVIEW_DELETED, CANDIDATE_REMOVED, COMPANY_DELETED
from app.storage import conversations

logger = logging.getLogger(__name__)


async def handle(event_type: str, data: dict) -> None:
    """company.deleted: the company's conversations go. candidate.removed and
    candidate.interview_deleted: the company's conversations that mention the erased candidate
    (their email or invite) or the deleted interview go. Safe on a redelivery: nothing is left to
    delete. Other events are ignored."""
    if event_type not in (COMPANY_DELETED, CANDIDATE_REMOVED, CANDIDATE_INTERVIEW_DELETED):
        return

    try:
        company_id = UUID(str(data.get("company_id")))
    except ValueError:
        # Retrying can't fix it: dropped, so Pub/Sub doesn't send it again and again.
        logger.warning("Dropped %s for a malformed company %r", event_type, data.get("company_id"))

        return

    if event_type == COMPANY_DELETED:
        deleted = await conversations.delete_company(company_id)
    elif event_type == CANDIDATE_REMOVED:
        needles = [str(data.get("email") or ""), str(data.get("candidate_invite_id") or "")]
        deleted = await conversations.delete_mentioning(company_id, needles)
    else:
        needles = [str(data.get("interview_id") or "")]
        deleted = await conversations.delete_mentioning(company_id, needles)

    if deleted:
        logger.info("Deleted %d assistant conversations (%s)", deleted, event_type)
