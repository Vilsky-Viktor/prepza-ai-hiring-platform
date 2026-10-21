from datetime import datetime

from prepza_common.db import delete_in_batches
from sqlalchemy import select
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


async def since(after: datetime) -> list[Erasure]:
    async with Session() as session:
        return list(await session.scalars(select(Erasure).where(Erasure.erased_at >= after)))


async def forget(before: datetime) -> int:
    return await delete_in_batches(Session, Erasure, Erasure.erased_at < before)
