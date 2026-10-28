"""Library's events: answers and scored topics for the questions' statistics, deleted guests and
fixed bank questions (rule 11: each is safe to repeat and in any order; an error answers 5xx and
Pub/Sub delivers it again)."""

from library.constants.events import ANSWER_RECORDED, GUESTS_DELETED, QUESTION_FIXED, SESSION_SCORED
from library.handlers import answer_recorded, guests_deleted, question_fixed, session_scored

HANDLERS = {
    ANSWER_RECORDED: answer_recorded.handle,
    SESSION_SCORED: session_scored.handle,
    GUESTS_DELETED: guests_deleted.handle,
    QUESTION_FIXED: question_fixed.handle,
}


async def handle(event_id: str, event_type: str, data: dict) -> None:
    """Other event types aren't library's (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(event_id, data)
