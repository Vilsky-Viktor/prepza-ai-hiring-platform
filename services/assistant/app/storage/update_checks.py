from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.models.updates import UpdateCheck
from app.storage.db import Session


async def last(connection_id: str) -> datetime | None:
    """When the connection last called get_updates; None before its first call."""
    async with Session() as session:
        return await session.scalar(
            select(UpdateCheck.checked_at).where(UpdateCheck.connection_id == connection_id)
        )


async def save(connection_id: str, at: datetime) -> None:
    """Its call at `at` is its last; a later one already saved stays."""
    query = insert(UpdateCheck).values(connection_id=connection_id, checked_at=at)
    query = query.on_conflict_do_update(
        index_elements=["connection_id"],
        set_={"checked_at": at},
        where=UpdateCheck.checked_at < at,
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def delete_before(before: datetime) -> int:
    """Checks older than `before` (connections or keys long unused, or gone): how many went."""
    async with Session() as session:
        deleted = await session.execute(delete(UpdateCheck).where(UpdateCheck.checked_at < before))
        await session.commit()

        return deleted.rowcount
