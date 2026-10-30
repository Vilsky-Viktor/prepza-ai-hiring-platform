import uuid

from fastapi import HTTPException, status
from prepza_common.limits.rate_limit import hit_or_skip
from sqlalchemy.exc import IntegrityError

from library.core.db import Session
from library.integrations.redis import get_redis
from library.repositories import bank, feedback
from library.services.quality import review


async def rate(question_id: uuid.UUID, user_id: str, value: int) -> None:
    """Sets the user's thumbs up or down, then reviews the question."""
    key = f"rate:ratings:{user_id}"
    await hit_or_skip(get_redis(), key, "RATINGS_PER_DAY", user_id=user_id)

    async with Session.begin() as session:
        await feedback.rate_question(session, question_id, user_id, value)

    await review(question_id)


async def report(question_id: uuid.UUID, user_id: str, reason: str, comment: str) -> None:
    """One report per user and question, whatever its revision. One already made is refused
    before it's counted; the count is against floods (with Redis down, not counted)."""
    async with Session() as session:
        reported = await feedback.has_reported(session, question_id, user_id)

    if reported:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reported")

    key = f"rate:reports:{user_id}"
    await hit_or_skip(get_redis(), key, "REPORTS_PER_DAY", user_id=user_id)

    try:
        async with Session.begin() as session:
            saved = await feedback.report_question(session, question_id, user_id, reason, comment)

            # Reported, it leaves the shared bank for everyone, with what it's a copy of.
            if saved:
                await bank.leave(session, [question_id])
    except IntegrityError:
        # The transaction is over: a report made before reporters were kept.
        saved = False

    if not saved:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reported")

    await review(question_id)
