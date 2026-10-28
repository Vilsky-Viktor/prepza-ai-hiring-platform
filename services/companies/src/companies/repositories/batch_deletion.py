from prepza_common.config.constants import DELETE_BATCH
from sqlalchemy import delete, select

from companies.constants.invites import InviteStatus
from companies.core.db import Session
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import guests


async def delete_invites(*conditions) -> list[tuple]:
    """Deletes the invites matching `conditions`, DELETE_BATCH at a time, each batch in its own
    transaction with guests.deleted for its guests; a deletion cut off midway goes on when run
    again. Returns (interview id, email, status, hold key) of those not finished."""
    unfinished = []

    while True:
        async with Session() as session:
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
            unfinished += [tuple(row) for row in removed if row.status != InviteStatus.FINISHED]
            await session.commit()

        if len(invite_ids) < DELETE_BATCH:
            return unfinished


async def delete_interviews(company_id) -> None:
    """Deletes the company's interviews, DELETE_BATCH at a time, each batch in its own
    transaction; an invite made meanwhile goes with its interview (cascade), its guest
    announced."""
    while True:
        async with Session() as session:
            chosen = select(Interview.id).where(Interview.company_id == company_id)
            interview_ids = list(await session.scalars(chosen.limit(DELETE_BATCH)))
            await guests.announce_deleted(session, CandidateInvite.interview_id.in_(interview_ids))
            await session.execute(delete(Interview).where(Interview.id.in_(interview_ids)))
            await session.commit()

        if len(interview_ids) < DELETE_BATCH:
            return
