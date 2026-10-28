import uuid

from sqlalchemy import func, literal, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from library.helpers.quality import replacement
from library.models.feedback import QuestionReport
from library.models.quality import QuestionRevision, QuestionStats
from library.models.sets import Question, QuestionSet, Topic


async def flagged(session: AsyncSession, offset: int, limit: int) -> list:
    """Questions flagged now, newest first, with their set and statistics."""
    reports = (
        select(func.count()).where(QuestionReport.question_id == Question.id).scalar_subquery()
    )
    query = (
        select(Question, QuestionStats, QuestionSet, reports.label("reports"))
        .join(QuestionStats, QuestionStats.question_id == Question.id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(QuestionSet, QuestionSet.id == Topic.set_id)
        .where(QuestionStats.flag.is_not(None))
        .order_by(QuestionStats.updated_at.desc(), Question.id)
        .offset(offset)
        .limit(limit)
    )

    return list(await session.execute(query))


async def replaced(session: AsyncSession, after: uuid.UUID | None, limit: int) -> list:
    """Questions the verifier or an owner replaced, newest first, `limit` after the revision
    `after` (paged by key: the list grows across every company): the old content, its set, and
    what replaced it — the question's next kept revision, or its current content if it hasn't
    been replaced again since."""
    order = (QuestionRevision.replaced_at, QuestionRevision.id)
    query = (
        select(QuestionRevision, QuestionSet, Question)
        .join(Question, Question.id == QuestionRevision.question_id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(QuestionSet, QuestionSet.id == Topic.set_id)
        .order_by(*(column.desc() for column in order))
        .limit(limit)
    )

    if after is not None:
        at = select(QuestionRevision.replaced_at).where(QuestionRevision.id == after)
        query = query.where(tuple_(*order) < tuple_(at.scalar_subquery(), literal(after)))

    rows = list(await session.execute(query))
    later = await session.scalars(
        select(QuestionRevision)
        .where(QuestionRevision.question_id.in_({row[0].question_id for row in rows}))
        .order_by(QuestionRevision.replaced_at, QuestionRevision.id)
    )
    versions = list(later)

    return [
        (revision, question_set, replacement(revision, question, versions))
        for revision, question_set, question in rows
    ]


async def revision(session: AsyncSession, revision_id) -> QuestionRevision | None:
    return await session.get(QuestionRevision, revision_id)
