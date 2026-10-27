from datetime import UTC, datetime

from prepza_common.events import outbox
from sqlalchemy import select

from app.constants.events import CANDIDATE_REMINDED
from app.constants.invites import REMINDERS_PER_RUN, InviteStatus
from app.helpers.logos import logo_path
from app.models.companies import Company
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def remind_unstarted(before: datetime) -> int:
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

    async with Session() as session:
        rows = (await session.execute(query)).all()

        for invite, interview, company in rows:
            invite.reminded_at = datetime.now(UTC)
            outbox.add(
                session,
                OutboxEvent,
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

        await session.commit()

    return len(rows)
