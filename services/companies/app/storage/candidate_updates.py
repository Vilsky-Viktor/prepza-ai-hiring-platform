from datetime import datetime

from sqlalchemy import and_, or_, select

from app.constants.invites import InviteStatus
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.storage.db import Session


def between(column, since: datetime, until: datetime):
    return and_(column > since, column <= until)


async def changed(
    company_ids: list, since: datetime, until: datetime
) -> list[tuple[CandidateInvite, Interview]]:
    """The companies' candidates who started, finished or whose invite wasn't delivered after
    `since` and up to `until`, with their interviews; erased candidates aren't among them."""
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(
            Interview.company_id.in_(company_ids),
            CandidateInvite.status != InviteStatus.DELETED,
            or_(
                between(CandidateInvite.started_at, since, until),
                between(CandidateInvite.finished_at, since, until),
                between(CandidateInvite.undelivered_at, since, until),
            ),
        )
    )

    async with Session() as session:
        return list(await session.execute(query))
