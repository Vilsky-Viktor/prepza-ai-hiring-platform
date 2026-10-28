from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from billing.models.billing import Entry


async def page(
    session: AsyncSession, owner_type: str, owner_id: str, offset: int, limit: int
) -> list[Entry]:
    """A wallet's movements, newest first."""
    query = (
        select(Entry)
        .where(Entry.owner_type == owner_type, Entry.owner_id == owner_id)
        .order_by(Entry.created_at.desc(), Entry.id)
        .offset(offset)
        .limit(limit)
    )

    return list(await session.scalars(query))
