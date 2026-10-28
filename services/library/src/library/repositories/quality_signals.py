import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.feedback import QuestionRating, QuestionReport
from library.models.quality import QuestionRevision, QuestionStats
from library.models.sets import Question


async def flagged_since(
    session: AsyncSession, since: datetime, limit: int
) -> list[tuple[Question, QuestionStats]]:
    """Questions flagged now whose flag was set (or sent again) since `since`, newest first."""
    query = (
        select(Question, QuestionStats)
        .join(QuestionStats, QuestionStats.question_id == Question.id)
        .where(QuestionStats.flag.is_not(None), QuestionStats.flagged_at >= since)
        .order_by(QuestionStats.flagged_at.desc(), Question.id)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def feedback(session: AsyncSession, question_ids: list[uuid.UUID]) -> tuple[dict, dict]:
    """Each question's reports per reason, and its (likes, dislikes)."""
    reports = (
        select(QuestionReport.question_id, QuestionReport.reason, func.count())
        .where(QuestionReport.question_id.in_(question_ids))
        .group_by(QuestionReport.question_id, QuestionReport.reason)
    )
    ratings = (
        select(
            QuestionRating.question_id,
            func.count().filter(QuestionRating.value == 1),
            func.count().filter(QuestionRating.value == -1),
        )
        .where(QuestionRating.question_id.in_(question_ids))
        .group_by(QuestionRating.question_id)
    )
    reasons = {}

    for question_id, reason, count in await session.execute(reports):
        reasons.setdefault(question_id, {})[reason] = count

    votes = {row[0]: (row[1], row[2]) for row in await session.execute(ratings)}

    return reasons, votes


async def replaced_since(
    session: AsyncSession, since: datetime, limit: int
) -> list[tuple[QuestionRevision, Question]]:
    """Revisions kept since `since`, newest first, with their question as it is now."""
    query = (
        select(QuestionRevision, Question)
        .join(Question, Question.id == QuestionRevision.question_id)
        .where(QuestionRevision.replaced_at >= since)
        .order_by(QuestionRevision.replaced_at.desc(), QuestionRevision.id)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def revisions_of(
    session: AsyncSession, question_ids: set[uuid.UUID]
) -> list[QuestionRevision]:
    """Every revision of these questions, oldest first."""
    query = (
        select(QuestionRevision)
        .where(QuestionRevision.question_id.in_(question_ids))
        .order_by(QuestionRevision.replaced_at, QuestionRevision.id)
    )

    return list(await session.scalars(query))
