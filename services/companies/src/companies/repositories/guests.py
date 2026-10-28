from prepza_common.config.constants import GUEST_UID_PREFIX
from prepza_common.events import outbox
from sqlalchemy import select

from companies.constants.events import GUESTS_DELETED
from companies.models.invites import CandidateInvite
from companies.models.outbox import OutboxEvent


async def announce_deleted(session, *conditions) -> None:
    """Saves guests.deleted, in the caller's transaction, for the guest invites matching
    `conditions` that it's about to delete: each guest's own sign-in goes with its invite."""
    invite_ids = await session.scalars(
        select(CandidateInvite.id).where(CandidateInvite.guest.is_(True), *conditions)
    )
    user_ids = [f"{GUEST_UID_PREFIX}{invite_id}" for invite_id in invite_ids]

    if user_ids:
        outbox.add(session, OutboxEvent, GUESTS_DELETED, {"user_ids": user_ids})
