from datetime import datetime
from uuid import UUID

from prepza_common.db.db import delete_in_batches
from sqlalchemy import select

from app.models.invites import CandidateInvite
from app.models.removals import RemovedInvite
from app.storage.db import Session


async def restored(after: datetime, limit: int) -> list[tuple[CandidateInvite, UUID]]:
    """Up to `limit` invites erased since `after` that are back (a restored backup), each with
    its company; erasing one again takes it out of the next read."""
    query = (
        select(CandidateInvite, RemovedInvite.company_id)
        .join(RemovedInvite, RemovedInvite.invite_id == CandidateInvite.id)
        .where(RemovedInvite.removed_at >= after)
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def forget(before: datetime) -> int:
    return await delete_in_batches(Session, RemovedInvite, RemovedInvite.removed_at < before)
