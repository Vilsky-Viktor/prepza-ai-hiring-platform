from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testee_common.db.db import delete_in_batches

from assistant.models.updates import UpdateCheck


async def last(session: AsyncSession, connection_id: str) -> datetime | None:
    """When the connection last called get_updates; None before its first call."""
    return await session.scalar(
        select(UpdateCheck.checked_at).where(UpdateCheck.connection_id == connection_id)
    )


async def save(session: AsyncSession, connection_id: str, at: datetime) -> None:
    """Its call at `at` is its last; a later one already saved stays."""
    query = insert(UpdateCheck).values(connection_id=connection_id, checked_at=at)
    query = query.on_conflict_do_update(
        index_elements=["connection_id"],
        set_={"checked_at": at},
        where=UpdateCheck.checked_at < at,
    )

    await session.execute(query)


async def delete_connections(session: AsyncSession, connection_ids: list[str]) -> None:
    """The checks of these connections (a deleted account's). Safe to repeat."""
    await session.execute(delete(UpdateCheck).where(UpdateCheck.connection_id.in_(connection_ids)))


async def delete_before(sessions: async_sessionmaker, before: datetime) -> int:
    """Checks older than `before` (connections or keys long unused, or gone): how many went, in
    batches."""
    return await delete_in_batches(sessions, UpdateCheck, UpdateCheck.checked_at < before)
