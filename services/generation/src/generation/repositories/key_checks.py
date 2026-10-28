import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from generation.models.key_checks import KeyCheck


async def add(
    session: AsyncSession, question_id: uuid.UUID, question_text: str, marked_answer: str
) -> None:
    """Queues a check; a question already waiting keeps its place."""
    statement = (
        insert(KeyCheck)
        .values(question_id=question_id, question_text=question_text, marked_answer=marked_answer)
        .on_conflict_do_nothing()
    )
    await session.execute(statement)


async def unsent(session: AsyncSession, limit: int) -> list[KeyCheck]:
    """Up to `limit` checks waiting to be sent, oldest first."""
    query = (
        select(KeyCheck)
        .where(KeyCheck.batch_id.is_(None))
        .order_by(KeyCheck.created_at)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def sent_batches(session: AsyncSession) -> list[str]:
    query = select(KeyCheck.batch_id).where(KeyCheck.batch_id.is_not(None)).distinct()

    return list(await session.scalars(query))


async def in_batch(session: AsyncSession, batch_id: str) -> list[KeyCheck]:
    return list(await session.scalars(select(KeyCheck).where(KeyCheck.batch_id == batch_id)))


async def set_batch(
    session: AsyncSession, question_ids: list[uuid.UUID], batch_id: str | None
) -> None:
    """Marks checks as sent in a batch, or with None as waiting to be sent again."""
    await session.execute(
        update(KeyCheck).where(KeyCheck.question_id.in_(question_ids)).values(batch_id=batch_id)
    )


async def remove(session: AsyncSession, question_ids: list[uuid.UUID]) -> None:
    await session.execute(delete(KeyCheck).where(KeyCheck.question_id.in_(question_ids)))
