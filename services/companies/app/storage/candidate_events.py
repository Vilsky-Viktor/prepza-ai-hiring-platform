import uuid

from prepza_common.events import outbox
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interviews import Interview
from app.models.outbox import OutboxEvent


async def add(
    session: AsyncSession, event_type: str, invite_id: uuid.UUID, interview_id: uuid.UUID
) -> None:
    """Saves a candidate's event (started, undelivered, expired) for the API's web hooks with
    the change that caused it: which candidate, of which interview and company."""
    company_id = await session.scalar(
        select(Interview.company_id).where(Interview.id == interview_id)
    )
    outbox.add(
        session,
        OutboxEvent,
        event_type,
        {
            "company_id": str(company_id),
            "interview_id": str(interview_id),
            "candidate_invite_id": str(invite_id),
        },
    )
