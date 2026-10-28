import uuid
from datetime import UTC, datetime

from rounds.constants.rounds import EXPIRY_BATCH, RoundStatus
from rounds.repositories import session_expiry, sessions
from rounds.services import outbox as outbox_service


async def finish_invite(invite_id: uuid.UUID) -> None:
    """Finishes every open section of the interview; unanswered questions count as wrong."""
    for row in await sessions.list_for_invite(invite_id):
        if row.status == RoundStatus.IN_PROGRESS:
            await sessions.finish(row.id)

    await outbox_service.flush_quietly()


async def finish_expired() -> int:
    """Finishes interviews whose time ran out while the candidate was away."""
    expired = await session_expiry.expired_invites(datetime.now(UTC), EXPIRY_BATCH)

    for invite_id in expired:
        await finish_invite(invite_id)

    return len(expired)


async def finish_if_expired(invite_id: uuid.UUID) -> bool:
    """For a candidate coming back: their interview ends at once if its time ran out."""
    if not await session_expiry.expired_invites(datetime.now(UTC), 1, invite_id):
        return False

    await finish_invite(invite_id)

    return True
