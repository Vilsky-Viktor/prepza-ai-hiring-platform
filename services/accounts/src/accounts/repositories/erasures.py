from datetime import datetime

from prepza_common.db.db import delete_in_batches
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from accounts.models.erasures import Erasure


async def record(session: AsyncSession, user_id: str, email: str) -> None:
    """Once per account: a deletion run again keeps its first time."""
    await session.execute(
        insert(Erasure).values(user_id=user_id, email=email).on_conflict_do_nothing()
    )


async def page(
    session: AsyncSession, after: datetime, below: tuple[datetime, str] | None, size: int
) -> list[Erasure]:
    """Up to `size` erasures made since `after`, newest first, those before `below` (the last
    one of the previous page, as erased_at and user_id) when given."""
    query = select(Erasure).where(Erasure.erased_at >= after)

    if below is not None:
        query = query.where(tuple_(Erasure.erased_at, Erasure.user_id) < below)

    query = query.order_by(Erasure.erased_at.desc(), Erasure.user_id.desc()).limit(size)

    return list(await session.scalars(query))


async def forget(sessions: async_sessionmaker, before: datetime) -> int:
    """Batched: each batch its own transaction, from `sessions` (the service's factory)."""
    return await delete_in_batches(sessions, Erasure, Erasure.erased_at < before)
