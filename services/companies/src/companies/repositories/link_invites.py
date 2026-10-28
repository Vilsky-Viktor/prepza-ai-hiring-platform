import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_JOINED
from companies.constants.invites import InviteStatus
from companies.helpers.candidates import new_hold_key
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import outbox
from companies.repositories.interviews import company_of


async def for_link(
    session: AsyncSession,
    interview_id,
    email: str,
    hold_key: str | None = None,
    details: dict | None = None,
) -> CandidateInvite:
    """The candidate who came through the test's link: their invite, made now if it's new (with
    `hold_key`, its credits' key). A new one saves the event that emails them its link, to
    continue if they leave, with `details` (the test's title, company, language and logo
    path)."""
    email = email.lower()
    statement = (
        insert(CandidateInvite)
        .values(
            id=uuid.uuid4(),
            interview_id=interview_id,
            company_id=company_of(interview_id),
            email=email,
            token=secrets.token_urlsafe(32),
            status=InviteStatus.INVITED,
            created_at=datetime.now(UTC),
            sent_at=datetime.now(UTC),
            hold_key=hold_key or new_hold_key(interview_id),
        )
        .on_conflict_do_nothing(index_elements=["interview_id", "email"])
        .returning(CandidateInvite.id)
    )

    made = await session.scalar(statement)
    invite = await session.scalar(
        select(CandidateInvite).where(
            CandidateInvite.interview_id == interview_id, CandidateInvite.email == email
        )
    )

    # Only the request that made it: one email, also when two start at once.
    if made and details:
        company_id = await session.scalar(
            select(Interview.company_id).where(Interview.id == interview_id)
        )
        data = {
            "invite_id": str(invite.id),
            "company_id": str(company_id),
            "email": email,
            "token": invite.token,
            **details,
        }
        outbox.add(session, CANDIDATE_JOINED, data)

    return invite
