import uuid

from rounds.core.db import Session
from rounds.repositories import sessions


async def remove_invites(candidate_invite_ids: list[uuid.UUID]) -> None:
    """Companies' retention: candidates' sessions go with their expired invites."""
    if not candidate_invite_ids:
        return

    async with Session.begin() as session:
        await sessions.remove_for_invites(session, candidate_invite_ids)


async def remove_interview(interview_set_id: uuid.UUID) -> None:
    """Before companies deletes an interview: every candidate's sessions on it, a batch at a
    time; safe to repeat."""
    await sessions.remove_for_interview(Session, interview_set_id)
