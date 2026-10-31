from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import DELETE_BATCH

from companies.constants.invites import InviteStatus
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import guests
from companies.repositories.interviews import add_interview_deleted


async def delete_invites_batch(session: AsyncSession, *conditions) -> tuple[int, list[tuple]]:
    """Deletes up to DELETE_BATCH of the invites matching `conditions`, with guests.deleted for
    their guests. Returns how many went, and (interview id, email, status, hold key) of those
    not finished."""
    chosen = select(CandidateInvite.id).where(*conditions).limit(DELETE_BATCH)
    invite_ids = list(await session.scalars(chosen))
    await guests.announce_deleted(session, CandidateInvite.id.in_(invite_ids))
    removed = await session.execute(
        delete(CandidateInvite)
        .where(CandidateInvite.id.in_(invite_ids))
        .returning(
            CandidateInvite.interview_id,
            CandidateInvite.email,
            CandidateInvite.status,
            CandidateInvite.hold_key,
        )
    )
    unfinished = [tuple(row) for row in removed if row.status != InviteStatus.FINISHED]

    return len(invite_ids), unfinished


async def delete_interviews_batch(session: AsyncSession, company_id) -> int:
    """Deletes up to DELETE_BATCH of the company's interviews, each with interview.deleted (so
    rounds and library delete its sessions and questions); an invite made meanwhile goes with
    its interview (cascade), its guest announced. Returns how many went."""
    chosen = select(Interview.id).where(Interview.company_id == company_id)
    interview_ids = list(await session.scalars(chosen.limit(DELETE_BATCH)))
    await guests.announce_deleted(session, CandidateInvite.interview_id.in_(interview_ids))
    gone = await session.execute(
        delete(Interview)
        .where(Interview.id.in_(interview_ids))
        .returning(Interview.id, Interview.company_id, Interview.set_id, Interview.generation_id)
    )

    for row in gone:
        add_interview_deleted(session, *row)

    return len(interview_ids)
