import uuid

from rounds.core.db import Session
from rounds.repositories import sessions, voice_clips


async def remove_invites(candidate_invite_ids: list[uuid.UUID]) -> None:
    """Companies' retention: candidates' sessions go with their expired invites."""
    if not candidate_invite_ids:
        return

    async with Session.begin() as session:
        await sessions.remove_for_invites(session, candidate_invite_ids)


async def remove_interview(interview_set_id: uuid.UUID) -> None:
    """A deleted interview's sessions (interview.deleted): every candidate's and preview's on
    it, a batch at a time; safe to repeat, so a redelivered event deletes nothing more."""
    await sessions.remove_for_interview(Session, interview_set_id)


async def remove_company(company_id: uuid.UUID) -> None:
    """A deleted company's sessions (company.deleted), as remove_interview; also those of an
    interview whose own event came first or never named its set; and its questions read aloud
    in voice mode."""
    await sessions.remove_for_company(Session, company_id)
    await voice_clips.remove_for_company(Session, company_id)
