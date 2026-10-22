from datetime import datetime

from prepza_common.db import delete_in_batches
from sqlalchemy import select

from app.models.removals import RemovedInvite
from app.storage.db import Session


async def since(after: datetime) -> list[RemovedInvite]:
    async with Session() as session:
        query = select(RemovedInvite).where(RemovedInvite.removed_at >= after)

        return list(await session.scalars(query))


async def forget(before: datetime) -> int:
    return await delete_in_batches(Session, RemovedInvite, RemovedInvite.removed_at < before)
