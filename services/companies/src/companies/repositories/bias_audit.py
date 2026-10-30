"""The bias-audit export's candidates: those who finished with a grade, in one company, one of
its interviews or a span of finishing times."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.invites import InviteStatus
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite


def scope(company_id, interview_id, start: datetime | None, end: datetime | None) -> list:
    """The company's finished candidates; only one interview's, or those finished from `start`
    and before `end`, when given."""
    filters = [
        CandidateInvite.company_id == company_id,
        CandidateInvite.status == InviteStatus.FINISHED,
    ]

    if interview_id is not None:
        filters.append(CandidateInvite.interview_id == interview_id)

    if start is not None:
        filters.append(CandidateInvite.finished_at >= start)

    if end is not None:
        filters.append(CandidateInvite.finished_at < end)

    return filters


async def outcomes(session: AsyncSession, filters: list, offset: int, limit: int) -> list:
    """A batch of (invite, interview) pairs with a grade, by interview and finishing time."""
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(*filters, CandidateInvite.grade.is_not(None))
        .order_by(CandidateInvite.interview_id, CandidateInvite.finished_at, CandidateInvite.id)
        .offset(offset)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def unscored(session: AsyncSession, filters: list) -> list:
    """Finished candidates in the scope whose grade isn't stored yet."""
    query = select(CandidateInvite.id).where(*filters, CandidateInvite.grade.is_(None))

    return list(await session.scalars(query))
