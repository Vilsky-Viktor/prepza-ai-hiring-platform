import uuid
from datetime import UTC, datetime

from rounds.constants.rounds import EXPIRY_BATCH
from rounds.core.db import Session
from rounds.repositories import session_expiry, sessions
from rounds.services import outbox as outbox_service
from rounds.services import sections


async def finish_invite(invite_id: uuid.UUID) -> None:
    """Finishes every open section of the interview, all in one save; unanswered questions count
    as wrong."""
    async with Session.begin() as session:
        await sections.finish_open(session, await sessions.list_for_invite(session, invite_id))

    await outbox_service.flush_quietly()


async def expired(now: datetime, limit: int, invite_id: uuid.UUID | None = None) -> list[uuid.UUID]:
    async with Session() as session:
        return await session_expiry.expired_invites(session, now, limit, invite_id)


async def finish_expired() -> int:
    """Finishes interviews whose time ran out while the candidate was away."""
    found = await expired(datetime.now(UTC), EXPIRY_BATCH)

    for invite_id in found:
        await finish_invite(invite_id)

    return len(found)


async def finish_if_expired(invite_id: uuid.UUID) -> bool:
    """For a candidate coming back: their interview ends at once if its time ran out."""
    if not await expired(datetime.now(UTC), 1, invite_id):
        return False

    await finish_invite(invite_id)

    return True
