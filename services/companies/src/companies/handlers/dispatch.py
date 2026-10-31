"""Companies' events: other services' actions for the audit log, finished interviews (the
candidate's charge, grade and notice) and the interview generation's outcome (rule 11: each is
safe to repeat; processed events, claims and unique event ids keep a redelivery from changing
anything twice)."""

from datetime import datetime

from testee_common.events.audit_actions import AUDIT_RECORDED

from companies.constants.events import (
    GENERATION_CANCELLED,
    GENERATION_COMPLETED,
    GENERATION_FAILED,
    INTERVIEW_FINISHED,
)
from companies.handlers import (
    audit_recorded,
    generation_cancelled,
    generation_completed,
    generation_failed,
    interview_finished,
)

HANDLERS = {
    GENERATION_COMPLETED: generation_completed.handle,
    GENERATION_FAILED: generation_failed.handle,
    GENERATION_CANCELLED: generation_cancelled.handle,
    INTERVIEW_FINISHED: interview_finished.handle,
    AUDIT_RECORDED: audit_recorded.handle,
}


async def handle(event_type: str, data: dict, event_id: str, at: datetime) -> None:
    """`at` is when the event happened (its outbox row's time). Other event types aren't
    companies' (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data, event_id, at)
