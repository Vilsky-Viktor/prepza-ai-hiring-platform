"""The admin zone's stats from companies' records: what is stored now, so deleted companies and
candidates past retention aren't counted."""

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.db.stats import counted

from companies.constants.invites import InviteStatus
from companies.constants.verification import VerificationStatus
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite


async def stats(session: AsyncSession, period: str | None) -> dict[str, int]:
    """All time or in `period` (a year or a period): companies created and verified now (in the month approved),
    interviews created, and candidates invited and finished, both in the month they were invited."""
    invites = func.count(CandidateInvite.id)

    return {
        "companies": await counted(session, func.count(Company.id), Company.created_at, period),
        "verified": await counted(
            session,
            func.count(Company.id),
            Company.verification_decided_at,
            period,
            Company.verification_status == VerificationStatus.APPROVED,
        ),
        "interviews": await counted(
            session, func.count(Interview.id), Interview.created_at, period
        ),
        "invited": await counted(session, invites, CandidateInvite.created_at, period),
        "finished": await counted(
            session,
            invites,
            CandidateInvite.created_at,
            period,
            CandidateInvite.status == InviteStatus.FINISHED,
        ),
    }
