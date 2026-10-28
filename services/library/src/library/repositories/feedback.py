import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from library.core.db import Session
from library.models.feedback import QuestionRating, QuestionReport, QuestionReporter


async def rate_question(question_id: uuid.UUID, user_id: str, value: int) -> None:
    """Sets the user's thumbs up or down; voting again changes it."""
    statement = (
        insert(QuestionRating)
        .values(question_id=question_id, user_id=user_id, value=value)
        .on_conflict_do_update(
            index_elements=[QuestionRating.question_id, QuestionRating.user_id],
            set_={"value": value},
        )
    )

    async with Session() as session:
        await session.execute(statement)
        await session.commit()


async def my_question_rating(question_id: uuid.UUID, user_id: str) -> int | None:
    query = select(QuestionRating.value).where(
        QuestionRating.question_id == question_id, QuestionRating.user_id == user_id
    )

    async with Session() as session:
        return await session.scalar(query)


async def question_stats(question_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    """Likes, dislikes and reports per question; questions without feedback are missing."""
    ratings = (
        select(
            QuestionRating.question_id,
            func.count().filter(QuestionRating.value == 1),
            func.count().filter(QuestionRating.value == -1),
        )
        .where(QuestionRating.question_id.in_(question_ids))
        .group_by(QuestionRating.question_id)
    )
    reports = (
        select(QuestionReport.question_id, func.count())
        .where(QuestionReport.question_id.in_(question_ids))
        .group_by(QuestionReport.question_id)
    )
    stats = {}

    async with Session() as session:
        for question_id, likes, dislikes in await session.execute(ratings):
            stats[question_id] = {"likes": likes, "dislikes": dislikes, "reports": 0}

        for question_id, count in await session.execute(reports):
            stats.setdefault(question_id, {"likes": 0, "dislikes": 0, "reports": 0})
            stats[question_id]["reports"] = count

    return stats


async def list_reports(
    question_id: uuid.UUID, offset: int = 0, limit: int | None = None
) -> list[QuestionReport]:
    """Newest first; without a limit, every report (the verifier reads them all)."""
    query = (
        select(QuestionReport)
        .where(QuestionReport.question_id == question_id)
        .order_by(QuestionReport.created_at.desc(), QuestionReport.id)
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def report_question(question_id: uuid.UUID, user_id: str, reason: str, comment: str) -> bool:
    """False when the user has reported the question before, in this revision or an earlier one."""
    reporter = (
        insert(QuestionReporter)
        .values(question_id=question_id, user_id=user_id)
        .on_conflict_do_nothing()
        .returning(QuestionReporter.user_id)
    )

    async with Session() as session:
        if await session.scalar(reporter) is None:
            return False

        session.add(
            QuestionReport(question_id=question_id, user_id=user_id, reason=reason, comment=comment)
        )

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()

            return False

        return True


async def has_reported(question_id: uuid.UUID, user_id: str) -> bool:
    query = select(QuestionReporter.user_id).where(
        QuestionReporter.question_id == question_id, QuestionReporter.user_id == user_id
    )

    async with Session() as session:
        return await session.scalar(query) is not None
