import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.models.answers import Answer
from rounds.models.sessions import Session


async def for_sets(session: AsyncSession, set_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[int]]:
    """Candidates' answers per interview set: [timed out, all]. Previews and practice rounds
    stay out; sets without answers are left out."""
    query = (
        select(
            Session.interview_set_id,
            func.count(Answer.id).filter(Answer.timed_out),
            func.count(Answer.id),
        )
        .join(Answer, Answer.session_id == Session.id)
        .where(Session.interview_set_id.in_(set_ids), ~Session.preview, ~Session.practice)
        .group_by(Session.interview_set_id)
    )

    return {set_id: [timed_out, total] for set_id, timed_out, total in await session.execute(query)}
