from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_REMINDED
from companies.constants.invites import REMINDERS_PER_RUN, InviteStatus
from companies.helpers.logos import logo_path
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import outbox


async def remind_unstarted(session: AsyncSession, before: datetime) -> int:
    """Queues one reminder for each invite not started and last sent before `before`, and marks
    it reminded in the same transaction, so nobody is reminded twice. Returns how many."""
    query = (
        select(CandidateInvite, Interview, Company)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .join(Company, Company.id == Interview.company_id)
        .where(
            CandidateInvite.status == InviteStatus.INVITED,
            CandidateInvite.sent_at < before,
            CandidateInvite.reminded_at.is_(None),
            # A reminder names its interview: one without a stored title waits for it.
            Interview.title.is_not(None),
        )
        .limit(REMINDERS_PER_RUN)
        .with_for_update(of=CandidateInvite, skip_locked=True)
    )

    rows = (await session.execute(query)).all()

    for invite, interview, company in rows:
        invite.reminded_at = datetime.now(UTC)
        outbox.add(
            session,
            CANDIDATE_REMINDED,
            {
                "invite_id": str(invite.id),
                "company_id": str(company.id),
                "email": invite.email,
                "token": invite.token,
                "title": interview.title,
                "company": company.name,
                "language": interview.language,
                "logo_path": logo_path(company),
                "verified": company.verified_domain is not None,
            },
        )

    return len(rows)
