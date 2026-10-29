import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.feedback import QuestionRating, QuestionReport
from library.models.quality import QuestionRevision, QuestionStats
from library.models.sets import Question, QuestionSet, Topic


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


async def flagged_templates(
    session: AsyncSession,
) -> list[tuple[Question, QuestionStats, Topic, QuestionSet]]:
    """Platform templates' questions flagged now, with their topic and template, for the evals'
    traps (evals/scripts/export_flagged.py); never a company's question."""
    query = (
        select(Question, QuestionStats, Topic, QuestionSet)
        .join(QuestionStats, QuestionStats.question_id == Question.id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(QuestionSet, QuestionSet.id == Topic.set_id)
        .where(QuestionStats.flag.is_not(None), QuestionSet.company_id.is_(None))
        .order_by(Question.id)
    )

    return [tuple(row) for row in await session.execute(query)]


async def replaced_templates(
    session: AsyncSession,
) -> list[tuple[QuestionRevision, Question, Topic, QuestionSet]]:
    """Platform templates' questions replaced while flagged, as they were (the revision), with
    the question now, its topic and template, for the evals' traps; never a company's question."""
    query = (
        select(QuestionRevision, Question, Topic, QuestionSet)
        .join(Question, Question.id == QuestionRevision.question_id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(QuestionSet, QuestionSet.id == Topic.set_id)
        .where(QuestionRevision.flag.is_not(None), QuestionSet.company_id.is_(None))
        .order_by(QuestionRevision.replaced_at, QuestionRevision.id)
    )

    return [tuple(row) for row in await session.execute(query)]
