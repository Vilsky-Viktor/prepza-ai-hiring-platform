from testee_common.events.deletions import USER_DELETED

from ats.constants.events import (
    ATS_CANDIDATE_ARRIVED,
    CANDIDATE_FINISHED,
    CANDIDATE_REMOVED,
    COMPANY_DELETED,
    CREDITS_ADDED,
    INTERVIEW_DELETED,
    INTERVIEW_READY,
)
from ats.handlers import (
    ats_candidate_arrived,
    candidate_finished,
    candidate_removed,
    company_deleted,
    credits_added,
    interview_deleted,
    interview_ready,
    user_deleted,
)

HANDLERS = {
    ATS_CANDIDATE_ARRIVED: ats_candidate_arrived.handle,
    CANDIDATE_FINISHED: candidate_finished.handle,
    INTERVIEW_READY: interview_ready.handle,
    CANDIDATE_REMOVED: candidate_removed.handle,
    INTERVIEW_DELETED: interview_deleted.handle,
    COMPANY_DELETED: company_deleted.handle,
    CREDITS_ADDED: credits_added.handle,
    USER_DELETED: user_deleted.handle,
}


async def handle(event_type: str, data: dict) -> None:
    """Companies', billing's and accounts' events, and ats' own, each to its handler. Each is safe to run
    again on a redelivery: a report goes back once (reported_at), a candidate is invited once
    (the claim), and deleting twice deletes nothing more. Other events are ignored."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data)
