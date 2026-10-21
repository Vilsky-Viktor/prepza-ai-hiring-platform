from prepza_common import outbox
from prepza_common.constants import GUEST_UID_PREFIX
from sqlalchemy import select

from app.constants.events import GUESTS_DELETED
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent


async def announce_deleted(session, *conditions) -> None:
    """Saves guests.deleted, in the caller's transaction, for the guest invites matching
    `conditions` that it's about to delete: each guest's own sign-in goes with its invite."""
    invite_ids = await session.scalars(
        select(CandidateInvite.id).where(CandidateInvite.guest.is_(True), *conditions)
    )
    user_ids = [f"{GUEST_UID_PREFIX}{invite_id}" for invite_id in invite_ids]

    if user_ids:
        outbox.add(session, OutboxEvent, GUESTS_DELETED, {"user_ids": user_ids})
