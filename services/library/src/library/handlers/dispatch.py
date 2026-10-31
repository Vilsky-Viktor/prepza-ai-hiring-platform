"""Library's events: answers and scored topics for the questions' statistics, deleted guests,
fixed bank questions, companies' deleted interviews and companies, interviews kept out of the
shared bank or let back in, and accounts' deleted accounts (rule 11: each is safe to repeat and
in any order; an error answers 5xx and Pub/Sub delivers it again)."""

from testee_common.events.deletions import COMPANY_DELETED, INTERVIEW_DELETED, USER_DELETED
from testee_common.events.interviews import INTERVIEW_PRIVACY_CHANGED

from library.constants.events import ANSWER_RECORDED, GUESTS_DELETED, QUESTION_FIXED, SESSION_SCORED
from library.handlers import (
    answer_recorded,
    company_deleted,
    guests_deleted,
    interview_deleted,
    interview_privacy_changed,
    question_fixed,
    session_scored,
    user_deleted,
)

HANDLERS = {
    ANSWER_RECORDED: answer_recorded.handle,
    SESSION_SCORED: session_scored.handle,
    GUESTS_DELETED: guests_deleted.handle,
    QUESTION_FIXED: question_fixed.handle,
    INTERVIEW_DELETED: interview_deleted.handle,
    COMPANY_DELETED: company_deleted.handle,
    USER_DELETED: user_deleted.handle,
    INTERVIEW_PRIVACY_CHANGED: interview_privacy_changed.handle,
}


async def handle(event_id: str, event_type: str, data: dict) -> None:
    """Other event types aren't library's (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(event_id, data)
