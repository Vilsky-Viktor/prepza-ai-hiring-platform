import secrets
import uuid
from datetime import UTC, datetime

from prepza_common import outbox
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.events import CANDIDATE_INVITED, CANDIDATE_REMOVED
from app.constants.invites import InviteStatus
from app.helpers.candidates import new_hold_key
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent
from app.storage.db import Session


async def upsert(
    interview_id,
    email: str,
    title: str,
    company: str,
    language: str,
    logo_path: str | None = None,
    hold_key: str | None = None,
    name: str | None = None,
    verified: bool = False,
    return_url: str | None = None,
    sign_in: bool = True,
    theme: str | None = None,
) -> tuple[CandidateInvite, bool]:
    """Creates the invite (with `hold_key`, its credits' key, or a new one), or returns the existing one so it
    can be sent again, and saves the email's event with it. True when it revived an expired
    invite, whose credits were given back. `name`, the inviter's or the ATS's, fills a name not
    known yet: a name an owner or admin set stays, also when the same invite comes again."""
    email = email.lower()
    statement = (
        insert(CandidateInvite)
        .values(
            id=uuid.uuid4(),
            interview_id=interview_id,
            email=email,
            token=secrets.token_urlsafe(32),
            status=InviteStatus.INVITED,
            created_at=datetime.now(UTC),
            sent_at=datetime.now(UTC),
            hold_key=hold_key or new_hold_key(interview_id),
        )
        .on_conflict_do_nothing(index_elements=["interview_id", "email"])
    )

    this = (CandidateInvite.interview_id == interview_id, CandidateInvite.email == email)

    async with Session() as session:
        await session.execute(statement)
        # In SQL, so an owner's edit made meanwhile is never written over.
        await session.execute(
            update(CandidateInvite).where(*this, CandidateInvite.name.is_(None)).values(name=name)
        )
        invite = await session.scalar(select(CandidateInvite).where(*this))
        revived = invite.status == InviteStatus.EXPIRED

        # Sending again revives an undelivered or expired invite and restarts its 30 days.
        if invite.status in (InviteStatus.UNDELIVERED, InviteStatus.EXPIRED):
            invite.status = InviteStatus.INVITED

        invite.sent_at = datetime.now(UTC)
        # A caller that sends the candidate itself (no sign-in, the link is enough) gets no
        # emails: no reminder either, marked as reminded.
        invite.guest = not sign_in
        invite.reminded_at = None if sign_in else datetime.now(UTC)

        if return_url:
            invite.return_url = return_url

        if theme:
            invite.theme = theme

        company_id = await session.scalar(
            select(Interview.company_id).where(Interview.id == interview_id)
        )

        if not sign_in:
            await session.commit()

            return invite, revived

        outbox.add(
            session,
            OutboxEvent,
            CANDIDATE_INVITED,
            {
                "invite_id": str(invite.id),
                # Notifications skips an address that stopped this company's emails.
                "company_id": str(company_id),
                "email": invite.email,
                "token": invite.token,
                "title": title,
                "company": company,
                "language": language,
                # The company's logo for the top of the email, when it has one.
                "logo_path": logo_path,
                # Whether a superadmin verified the company: the email notes it when not.
                "verified": verified,
            },
        )
        await session.commit()

        return invite, revived


async def find(interview_id, email: str) -> CandidateInvite | None:
    """The email's invite to the interview, or None when it hasn't been invited."""
    query = select(CandidateInvite).where(
        CandidateInvite.interview_id == interview_id, CandidateInvite.email == email.lower()
    )

    async with Session() as session:
        return await session.scalar(query)


async def held(interview_id, email: str) -> tuple[str | None, str | None]:
    """The invite's status and its credits' key, or (None, None) when this email hasn't been
    invited."""
    found = await find(interview_id, email)

    return (found.status, found.hold_key) if found else (None, None)


async def status_of(interview_id, email: str) -> str | None:
    """The invite's status, or None when this email hasn't been invited."""
    return (await held(interview_id, email))[0]


async def statuses_of(interview_id, emails: list[str]) -> dict[str, str]:
    """The statuses of those of `emails` (lowercase) invited to the interview, by email."""
    query = select(CandidateInvite.email, CandidateInvite.status).where(
        CandidateInvite.interview_id == interview_id, CandidateInvite.email.in_(emails)
    )

    async with Session() as session:
        return dict((await session.execute(query)).all())


async def unfinished(interview_id) -> list[CandidateInvite]:
    """The interview's invites not finished yet."""
    query = select(CandidateInvite).where(
        CandidateInvite.interview_id == interview_id,
        CandidateInvite.status != InviteStatus.FINISHED,
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def get(invite_id: uuid.UUID) -> CandidateInvite | None:
    async with Session() as session:
        return await session.get(CandidateInvite, invite_id)


async def get_by_token(token: str) -> tuple[CandidateInvite, Interview] | None:
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(CandidateInvite.token == token)
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


async def remove(invite: CandidateInvite, company_id) -> str | None:
    """Deletes the invite (its link stops working) and tells the other services, which forget the
    candidate too: the company's notifications about them, the ATS's record of them. Returns its
    status as it was deleted."""
    async with Session() as session:
        removed = await session.scalar(
            delete(CandidateInvite)
            .where(CandidateInvite.id == invite.id)
            .returning(CandidateInvite.status)
        )
        outbox.add(
            session,
            OutboxEvent,
            CANDIDATE_REMOVED,
            {
                "company_id": str(company_id),
                "interview_id": str(invite.interview_id),
                "candidate_invite_id": str(invite.id),
                "email": invite.email,
            },
        )
        await session.commit()

    return removed


async def set_extra_time(invite_id: uuid.UUID, extra_time: int) -> None:
    async with Session() as session:
        await session.execute(
            update(CandidateInvite)
            .where(CandidateInvite.id == invite_id)
            .values(extra_time=extra_time)
        )
        await session.commit()


async def company_ids_for(email: str) -> list[str]:
    """The companies with an invite for the address, whatever its case."""
    query = (
        select(Interview.company_id)
        .join(CandidateInvite, CandidateInvite.interview_id == Interview.id)
        .where(CandidateInvite.email == email.strip().lower())
        .distinct()
    )

    async with Session() as session:
        return [str(company_id) for company_id in await session.scalars(query)]
