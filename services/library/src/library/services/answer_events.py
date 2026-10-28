import logging
import uuid

from library.constants.events import ANSWER_RECORDED, SESSION_SCORED
from library.constants.quality import MIN_ANSWERS
from library.core.db import Session
from library.helpers.quality import score_group
from library.repositories import answer_stats
from library.services.quality import review

logger = logging.getLogger(__name__)

# The payload is read before anything is stored: a malformed event is logged and dropped, since
# a retry would fail the same way until it's dead-lettered.
MALFORMED = (KeyError, TypeError, ValueError)


async def record_answer(event_id: str, data: dict) -> None:
    """Adds one answer to its question's statistics, and to its bank original's when it's a
    copy, so an original's signals add up across every test that uses it. Each event counts
    once, however often Pub/Sub delivers it."""
    try:
        # Events from before multi-answer questions carry one option and no credit.
        answer = (
            uuid.UUID(data["question_id"]),
            data["question_text"],
            list(data.get("options") or [data["option"]]),
            float(data.get("credit", 1.0 if data["correct"] else 0.0)),
        )
    except MALFORMED as error:
        logger.error("Dropped malformed %s event %s: %r", ANSWER_RECORDED, event_id, error)

        return

    # Counted only while the question still reads as answered (see RECORD_ANSWER_SQL).
    async with Session.begin() as session:
        shown = await answer_stats.record_answer(session, event_id, *answer)

    # Answers say nothing about a question shown fewer than MIN_ANSWERS times (flag_for,
    # too_slow), so its review would come out as the last one did: it's skipped.
    await review_each(
        [question_id for question_id, times in (shown or {}).items() if times >= MIN_ANSWERS]
    )


async def record_results(event_id: str, data: dict) -> None:
    """Adds one finished topic's results to its questions' statistics (and their bank
    originals'), in the candidate's score group. Each event counts once."""
    try:
        results = (score_group(data["final_score"]), list(data["answers"]))
    except MALFORMED as error:
        logger.error("Dropped malformed %s event %s: %r", SESSION_SCORED, event_id, error)

        return

    async with Session.begin() as session:
        counted = await answer_stats.record_results(session, event_id, *results)

    await review_each(counted)


async def review_each(counted: list[uuid.UUID] | None) -> None:
    """After the commit: a review never raises, and the question's next event repeats a failed
    one."""
    for question_id in counted or []:
        await review(question_id)
