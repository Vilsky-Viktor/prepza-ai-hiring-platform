from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.config.constants import GUEST_UID_PREFIX

from companies.constants.events import GUESTS_DELETED
from companies.models.invites import CandidateInvite
from companies.repositories import outbox


async def announce_deleted(session: AsyncSession, *conditions) -> None:
    """Saves guests.deleted, in the caller's transaction, for the guest invites matching
    `conditions` that it's about to delete: each guest's own sign-in goes with its invite."""
    invite_ids = await session.scalars(
        select(CandidateInvite.id).where(CandidateInvite.guest.is_(True), *conditions)
    )
    user_ids = [f"{GUEST_UID_PREFIX}{invite_id}" for invite_id in invite_ids]

    if user_ids:
        outbox.add(session, GUESTS_DELETED, {"user_ids": user_ids})
