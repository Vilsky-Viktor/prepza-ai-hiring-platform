import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from generation.constants.patterns import PatternStatus
from generation.models.patterns import QualityPattern


async def for_flag(session: AsyncSession, flag: str) -> list[QualityPattern]:
    """Every pattern of a flag, whatever its status, oldest first."""
    query = (
        select(QualityPattern)
        .where(QualityPattern.flag == flag)
        .order_by(QualityPattern.created_at, QualityPattern.id)
    )

    return list(await session.scalars(query))


async def add(session: AsyncSession, text: str, flag: str, question_count: int) -> None:
    session.add(
        QualityPattern(
            text=text,
            flag=flag,
            question_count=question_count,
            status=PatternStatus.PROPOSED,
        )
    )


async def seen(session: AsyncSession, pattern_id: uuid.UUID, question_count: int) -> None:
    """Found again: its count grows and it's seen now."""
    statement = (
        update(QualityPattern)
        .where(QualityPattern.id == pattern_id)
        .values(question_count=QualityPattern.question_count + question_count, last_seen=func.now())
    )
    await session.execute(statement)


async def by_status(
    session: AsyncSession, status: str, offset: int, limit: int
) -> list[QualityPattern]:
    """Patterns of a status, most recently seen first."""
    query = (
        select(QualityPattern)
        .where(QualityPattern.status == status)
        .order_by(QualityPattern.last_seen.desc(), QualityPattern.id)
        .offset(offset)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def review(
    session: AsyncSession, pattern_id: uuid.UUID, status: str, reviewed_by: str
) -> bool:
    """Approves or dismisses a proposed pattern; False when it isn't proposed (any more)."""
    statement = (
        update(QualityPattern)
        .where(QualityPattern.id == pattern_id, QualityPattern.status == PatternStatus.PROPOSED)
        .values(status=status, reviewed_by=reviewed_by, reviewed_at=func.now())
        .returning(QualityPattern.id)
    )

    return (await session.execute(statement)).first() is not None
