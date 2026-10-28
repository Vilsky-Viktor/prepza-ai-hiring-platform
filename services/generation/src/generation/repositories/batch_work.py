import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from generation.models.batch_work import BatchWork


async def add(
    session: AsyncSession,
    kind: str,
    subject_id: uuid.UUID,
    key: str,
    step: str,
    payload: dict,
    body: dict,
):
    """Queues a piece of work; one already waiting for the same subject (and language) keeps
    its place, so a repeated job adds nothing."""
    statement = (
        insert(BatchWork)
        .values(kind=kind, subject_id=subject_id, key=key, step=step, payload=payload, body=body)
        .on_conflict_do_nothing(constraint="uq_batch_work_kind_subject_id_key")
    )
    await session.execute(statement)


async def unsent(session: AsyncSession, limit: int) -> list[BatchWork]:
    """Up to `limit` pieces waiting to be sent, oldest first."""
    query = (
        select(BatchWork)
        .where(BatchWork.batch_id.is_(None))
        .order_by(BatchWork.created_at)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def sent_batches(session: AsyncSession) -> list[str]:
    query = select(BatchWork.batch_id).where(BatchWork.batch_id.is_not(None)).distinct()

    return list(await session.scalars(query))


async def in_batch(session: AsyncSession, batch_id: str) -> list[BatchWork]:
    return list(await session.scalars(select(BatchWork).where(BatchWork.batch_id == batch_id)))


async def set_batch(session: AsyncSession, ids: list[uuid.UUID], batch_id: str | None) -> None:
    """Marks pieces as sent in a batch, or with None as waiting to be sent again."""
    await session.execute(update(BatchWork).where(BatchWork.id.in_(ids)).values(batch_id=batch_id))


async def next_step(
    session: AsyncSession,
    work_id: uuid.UUID,
    batch_id: str,
    step: str,
    attempt: int,
    payload: dict,
    body: dict,
) -> None:
    """The piece's next call, waiting to be sent; only while it's still in `batch_id`, so a
    batch read twice moves it once."""
    await session.execute(
        update(BatchWork)
        .where(BatchWork.id == work_id, BatchWork.batch_id == batch_id)
        .values(step=step, attempt=attempt, payload=payload, body=body, batch_id=None)
    )


async def remove(session: AsyncSession, ids: list[uuid.UUID]) -> None:
    await session.execute(delete(BatchWork).where(BatchWork.id.in_(ids)))
