import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_EXPIRED
from companies.constants.invites import InviteStatus
from companies.models.invites import CandidateInvite
from companies.repositories import candidate_events


async def expiring(session: AsyncSession, before: datetime, limit: int) -> list[CandidateInvite]:
    """Up to `limit` invites never started and last sent before `before`."""
    rows = await session.scalars(
        select(CandidateInvite)
        .where(
            CandidateInvite.status.in_([InviteStatus.INVITED, InviteStatus.UNDELIVERED]),
            CandidateInvite.sent_at < before,
        )
        .order_by(CandidateInvite.sent_at)
        .limit(limit)
    )

    return list(rows)


async def mark_expired(session: AsyncSession, invite_id: uuid.UUID, before: datetime) -> bool:
    """Expires an invite that still hasn't started and wasn't sent again since `before`; False
    when it was started or sent again meanwhile."""
    marked = await session.scalar(
        update(CandidateInvite)
        .where(
            CandidateInvite.id == invite_id,
            CandidateInvite.status.in_([InviteStatus.INVITED, InviteStatus.UNDELIVERED]),
            CandidateInvite.sent_at < before,
        )
        .values(status=InviteStatus.EXPIRED)
        .returning(CandidateInvite.interview_id)
    )

    if marked is not None:
        await candidate_events.add(session, CANDIDATE_EXPIRED, invite_id, marked)

    return marked is not None
