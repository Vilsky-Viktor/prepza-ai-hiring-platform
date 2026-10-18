import uuid
from datetime import datetime

from prepza_common import outbox
from prepza_common.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import QuestionRating, QuestionReport
from app.models.outbox import OutboxEvent
from app.models.quality import QuestionRevision, QuestionStats
from app.models.sets import Question
from app.storage.db import Session


async def rating_counts(session: AsyncSession, question_id: uuid.UUID) -> tuple[int, int]:
    """Likes and dislikes."""
    query = select(
        func.count().filter(QuestionRating.value == 1),
        func.count().filter(QuestionRating.value == -1),
    ).where(QuestionRating.question_id == question_id)

    return tuple((await session.execute(query)).one())


async def load(
    question_id: uuid.UUID,
) -> tuple[Question, QuestionStats | None, dict[str, int], int, int] | None:
    """The question, its answer stats, report counts per reason, likes and dislikes."""
    reports = (
        select(QuestionReport.reason, func.count())
        .where(QuestionReport.question_id == question_id)
        .group_by(QuestionReport.reason)
    )

    async with Session() as session:
        question = await session.get(Question, question_id)

        if question is None:
            return None

        stats = await session.get(QuestionStats, question_id)
        likes, dislikes = await rating_counts(session, question_id)

        return (
            question,
            stats,
            dict((await session.execute(reports)).all()),
            likes,
            dislikes,
        )


async def save_flag(
    question_id: uuid.UUID, flag: str | None, kept: bool = False, notice: dict | None = None
) -> None:
    """Also for a question nobody has answered yet: reports alone can flag it. `notice` is the
    owner's notification, saved with the flag."""
    flagged_at = func.now() if flag is not None else None
    statement = (
        insert(QuestionStats)
        .values(
            question_id=question_id,
            answers=0,
            correct=0,
            option_picks={},
            flag=flag,
            kept=kept,
            flagged_at=flagged_at,
        )
        .on_conflict_do_update(
            index_elements=[QuestionStats.question_id],
            set_={"flag": flag, "kept": kept, "flagged_at": flagged_at},
        )
    )

    async with Session() as session:
        await session.execute(statement)

        if notice is not None:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()


async def change_flag(
    question_id: uuid.UUID, previous: str | None, flag: str, notice: dict | None = None
) -> bool:
    """Flags the question only if its flag is still `previous`, as read before; `notice`, the
    owner's notification, is saved with it. False when another event changed it meanwhile, so
    two events at once flag a question, notify and send it to the verifier once."""
    statement = (
        insert(QuestionStats)
        .values(
            question_id=question_id,
            answers=0,
            correct=0,
            option_picks={},
            flag=flag,
            kept=False,
            flagged_at=func.now(),
        )
        .on_conflict_do_update(
            index_elements=[QuestionStats.question_id],
            set_={"flag": flag, "kept": False, "flagged_at": func.now()},
            where=QuestionStats.flag.is_not_distinct_from(previous),
        )
        .returning(QuestionStats.question_id)
    )

    async with Session() as session:
        changed = (await session.execute(statement)).first() is not None

        if changed and notice is not None:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()

        return changed


async def current_flag(question_id: uuid.UUID) -> str | None:
    async with Session() as session:
        return await session.scalar(
            select(QuestionStats.flag).where(QuestionStats.question_id == question_id)
        )


async def take_stale_flags(before: datetime, limit: int) -> list[tuple[uuid.UUID, str]]:
    """Up to `limit` flags set or last sent before `before`, oldest first, each dated now so the
    next sweep waits for it again: (question_id, flag)."""
    stale = (
        select(QuestionStats.question_id)
        .where(QuestionStats.flag.is_not(None), QuestionStats.flagged_at < before)
        .order_by(QuestionStats.flagged_at)
        .limit(limit)
    )
    statement = (
        update(QuestionStats)
        .where(QuestionStats.question_id.in_(stale))
        .values(flagged_at=func.now())
        .returning(QuestionStats.question_id, QuestionStats.flag)
    )

    async with Session() as session:
        taken = [tuple(row) for row in await session.execute(statement)]
        await session.commit()

        return taken


async def archive(session: AsyncSession, question_id: uuid.UUID) -> None:
    """Moves a question's content, answer stats and feedback into a revision, in `session`.

    The caller then replaces the question; its new content starts with no feedback.
    """
    question = await session.get(Question, question_id)

    if question is None:
        return

    stats = await session.get(QuestionStats, question_id)
    likes, dislikes = await rating_counts(session, question_id)
    reports = await session.scalars(
        select(QuestionReport).where(QuestionReport.question_id == question_id)
    )
    session.add(
        QuestionRevision(
            question_id=question_id,
            text=question.text,
            options=question.options,
            answers=stats.answers if stats else 0,
            correct=stats.correct if stats else 0,
            option_picks=stats.option_picks if stats else {},
            flag=stats.flag if stats else None,
            likes=likes,
            dislikes=dislikes,
            reports=[
                {
                    "reason": report.reason,
                    "comment": report.comment,
                    "created_at": report.created_at.isoformat(),
                }
                for report in reports
            ],
        )
    )

    for model in (QuestionStats, QuestionRating, QuestionReport):
        await session.execute(delete(model).where(model.question_id == question_id))
