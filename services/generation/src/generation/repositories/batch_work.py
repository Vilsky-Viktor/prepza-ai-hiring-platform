import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from generation.core.db import Session
from generation.models.batch_work import BatchWork


async def add(kind: str, subject_id: uuid.UUID, key: str, step: str, payload: dict, body: dict):
    """Queues a piece of work; one already waiting for the same subject (and language) keeps
    its place, so a repeated job adds nothing."""
    statement = (
        insert(BatchWork)
        .values(kind=kind, subject_id=subject_id, key=key, step=step, payload=payload, body=body)
        .on_conflict_do_nothing(constraint="uq_batch_work_kind_subject_id_key")
    )

    async with Session() as session:
        await session.execute(statement)
        await session.commit()


async def unsent(limit: int) -> list[BatchWork]:
    """Up to `limit` pieces waiting to be sent, oldest first."""
    query = (
        select(BatchWork)
        .where(BatchWork.batch_id.is_(None))
        .order_by(BatchWork.created_at)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def sent_batches() -> list[str]:
    query = select(BatchWork.batch_id).where(BatchWork.batch_id.is_not(None)).distinct()

    async with Session() as session:
        return list(await session.scalars(query))


async def in_batch(batch_id: str) -> list[BatchWork]:
    async with Session() as session:
        return list(await session.scalars(select(BatchWork).where(BatchWork.batch_id == batch_id)))


async def set_batch(ids: list[uuid.UUID], batch_id: str | None) -> None:
    """Marks pieces as sent in a batch, or with None as waiting to be sent again."""
    async with Session() as session:
        await session.execute(
            update(BatchWork).where(BatchWork.id.in_(ids)).values(batch_id=batch_id)
        )
        await session.commit()


async def next_step(
    work_id: uuid.UUID, batch_id: str, step: str, attempt: int, payload: dict, body: dict
) -> None:
    """The piece's next call, waiting to be sent; only while it's still in `batch_id`, so a
    batch read twice moves it once."""
    async with Session() as session:
        await session.execute(
            update(BatchWork)
            .where(BatchWork.id == work_id, BatchWork.batch_id == batch_id)
            .values(step=step, attempt=attempt, payload=payload, body=body, batch_id=None)
        )
        await session.commit()


async def remove(ids: list[uuid.UUID]) -> None:
    async with Session() as session:
        await session.execute(delete(BatchWork).where(BatchWork.id.in_(ids)))
        await session.commit()
