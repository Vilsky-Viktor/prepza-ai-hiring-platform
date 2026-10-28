"""The invites behind a company's credits: the ones holding credits now, and the ones billing's
history names by the key of their credits."""

from sqlalchemy import func, select

from companies.constants.invites import OPEN, InviteStatus
from companies.core.db import Session
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite

# The key of an invite's credits (helpers/candidates.new_hold_key), which billing names it by.
HOLD_KEY = CandidateInvite.hold_key


async def count_holding(company_id) -> int:
    """How many of the company's invites have credits set aside."""
    query = (
        select(func.count())
        .select_from(CandidateInvite)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(Interview.company_id == company_id, CandidateInvite.status.in_(OPEN))
    )

    async with Session() as session:
        return await session.scalar(query)


async def holding(company_id, offset: int, limit: int) -> list[tuple[CandidateInvite, Interview]]:
    """The company's invites whose credits are set aside, newest first, each with its
    interview."""
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(Interview.company_id == company_id, CandidateInvite.status.in_(OPEN))
        .order_by(CandidateInvite.created_at.desc(), CandidateInvite.id)
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def by_hold_keys(company_id, keys: list[str]) -> dict[str, tuple[CandidateInvite, Interview]]:
    """The company's invites with these credit keys, by key, in one query. Removed invites, and
    those of candidates who deleted their account, aren't found."""
    if not keys:
        return {}

    query = (
        select(HOLD_KEY, CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(
            Interview.company_id == company_id,
            CandidateInvite.status != InviteStatus.DELETED,
            HOLD_KEY.in_(keys),
        )
    )

    async with Session() as session:
        return {key: (invite, interview) for key, invite, interview in await session.execute(query)}
