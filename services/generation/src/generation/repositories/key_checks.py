import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from generation.core.db import Session
from generation.models.key_checks import KeyCheck


async def add(question_id: uuid.UUID, question_text: str, marked_answer: str) -> None:
    """Queues a check; a question already waiting keeps its place."""
    statement = (
        insert(KeyCheck)
        .values(question_id=question_id, question_text=question_text, marked_answer=marked_answer)
        .on_conflict_do_nothing()
    )

    async with Session() as session:
        await session.execute(statement)
        await session.commit()


async def unsent(limit: int) -> list[KeyCheck]:
    """Up to `limit` checks waiting to be sent, oldest first."""
    query = (
        select(KeyCheck)
        .where(KeyCheck.batch_id.is_(None))
        .order_by(KeyCheck.created_at)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def sent_batches() -> list[str]:
    query = select(KeyCheck.batch_id).where(KeyCheck.batch_id.is_not(None)).distinct()

    async with Session() as session:
        return list(await session.scalars(query))


async def in_batch(batch_id: str) -> list[KeyCheck]:
    async with Session() as session:
        return list(await session.scalars(select(KeyCheck).where(KeyCheck.batch_id == batch_id)))


async def set_batch(question_ids: list[uuid.UUID], batch_id: str | None) -> None:
    """Marks checks as sent in a batch, or with None as waiting to be sent again."""
    async with Session() as session:
        await session.execute(
            update(KeyCheck).where(KeyCheck.question_id.in_(question_ids)).values(batch_id=batch_id)
        )
        await session.commit()


async def remove(question_ids: list[uuid.UUID]) -> None:
    async with Session() as session:
        await session.execute(delete(KeyCheck).where(KeyCheck.question_id.in_(question_ids)))
        await session.commit()
