import logging
from uuid import UUID

from app.constants.events import (
    ATS_CANDIDATE_ARRIVED,
    CANDIDATE_FINISHED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
    COMPANY_OWNER,
    CREDITS_ADDED,
    INTERVIEW_DELETED,
    INTERVIEW_READY,
)
from app.services import ats as integrations
from app.services import ats_candidates
from app.storage import ats, ats_links
from app.storage import ats_candidates as ats_candidates_storage

logger = logging.getLogger(__name__)


async def interview_deleted(interview_id: UUID) -> None:
    """Workable's notifications for the interview's linked jobs are cancelled (as far as Workable
    answers), then its links and candidates go."""
    for link, connection in await ats_links.interview_links(interview_id):
        if link.subscription_id:
            await integrations.unsubscribe(connection, [link.subscription_id])

    await ats_links.delete_interview(interview_id)


async def company_deleted(company_id: UUID) -> None:
    """What prepza set up in the company's ATSs is cancelled (as far as each answers), then its
    connections go, with their linked jobs and candidates."""
    subscriptions = await ats_links.subscriptions(company_id)

    for connection in await ats.connections(company_id):
        await integrations.release(connection, subscriptions)

    await ats.delete_company(company_id)


async def handle(event_type: str, data: dict) -> None:
    """Companies' and billing's events, and ats' own. Each is safe to run again on a redelivery: a report goes
    back once (reported_at), a candidate is invited once (the claim), and deleting twice deletes
    nothing more. Other events are ignored."""
    if event_type == ATS_CANDIDATE_ARRIVED:
        await ats_candidates.invite_arrived(data)
    elif event_type == CANDIDATE_FINISHED:
        await ats_candidates.report(data)
    elif event_type == INTERVIEW_READY:
        await ats_candidates.invite_waiting(UUID(data["interview_id"]))
    elif event_type == CANDIDATE_REMOVED:
        await ats_candidates_storage.delete_candidate(UUID(data["interview_id"]), data["email"])
    elif event_type == INTERVIEW_DELETED:
        await interview_deleted(UUID(data["interview_id"]))
    elif event_type == COMPANY_DELETED:
        await company_deleted(UUID(data["company_id"]))
    elif event_type == CREDITS_ADDED and data.get("owner_type") == COMPANY_OWNER:
        try:
            company_id = UUID(str(data.get("owner_id")))
        except ValueError:
            # Retrying can't fix it: dropped, so Pub/Sub doesn't send it again and again.
            logger.warning("Dropped credits.added for a malformed owner %r", data.get("owner_id"))

            return

        await ats_candidates.topped_up(company_id)
