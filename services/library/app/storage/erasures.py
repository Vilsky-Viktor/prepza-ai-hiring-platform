from datetime import datetime

from prepza_common.db.db import delete_in_batches
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert

from app.models.erasures import Erasure
from app.storage.db import Session


async def record(user_id: str, email: str) -> None:
    """Once per account: a deletion run again keeps its first time."""
    async with Session() as session:
        await session.execute(
            insert(Erasure).values(user_id=user_id, email=email).on_conflict_do_nothing()
        )
        await session.commit()


async def page(after: datetime, below: tuple[datetime, str] | None, size: int) -> list[Erasure]:
    """Up to `size` erasures made since `after`, newest first, those before `below` (the last
    one of the previous page, as erased_at and user_id) when given."""
    query = select(Erasure).where(Erasure.erased_at >= after)

    if below is not None:
        query = query.where(tuple_(Erasure.erased_at, Erasure.user_id) < below)

    query = query.order_by(Erasure.erased_at.desc(), Erasure.user_id.desc()).limit(size)

    async with Session() as session:
        return list(await session.scalars(query))


async def forget(before: datetime) -> int:
    return await delete_in_batches(Session, Erasure, Erasure.erased_at < before)
