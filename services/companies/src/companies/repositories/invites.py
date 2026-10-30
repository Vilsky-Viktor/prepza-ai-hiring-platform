import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_INVITED, CANDIDATE_REMOVED
from companies.constants.invites import InviteStatus
from companies.helpers.candidates import new_hold_key
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.models.removals import RemovedInvite
from companies.repositories import guests, outbox
from companies.repositories.interviews import company_of


async def upsert(
    session: AsyncSession,
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
    mode_chosen: bool = False,
    voice: bool | None = None,
) -> tuple[CandidateInvite, bool]:
    """Creates the invite (with `hold_key`, its credits' key, or a new one), or returns the
    existing one so it can be sent again, and saves the email's event with it. True when it revived an expired
    invite, whose credits were given back. `name`, the inviter's or the ATS's, fills a name not
    known yet: a name an owner or admin set stays, also when the same invite comes again. With
    `mode_chosen`, `voice` becomes the candidate's own mode (None: the interview's) unless they
    already started."""
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
    )

    this = (CandidateInvite.interview_id == interview_id, CandidateInvite.email == email)

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

    if mode_chosen and invite.status == InviteStatus.INVITED:
        invite.voice = voice

    company_id = await session.scalar(
        select(Interview.company_id).where(Interview.id == interview_id)
    )

    if not sign_in:
        return invite, revived

    outbox.add(
        session,
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

    return invite, revived


async def find(session: AsyncSession, interview_id, email: str) -> CandidateInvite | None:
    """The email's invite to the interview, or None when it hasn't been invited."""
    query = select(CandidateInvite).where(
        CandidateInvite.interview_id == interview_id, CandidateInvite.email == email.lower()
    )

    return await session.scalar(query)


async def held(session: AsyncSession, interview_id, email: str) -> tuple[str | None, str | None]:
    """The invite's status and its credits' key, or (None, None) when this email hasn't been
    invited."""
    found = await find(session, interview_id, email)

    return (found.status, found.hold_key) if found else (None, None)


async def status_of(session: AsyncSession, interview_id, email: str) -> str | None:
    """The invite's status, or None when this email hasn't been invited."""
    return (await held(session, interview_id, email))[0]


async def statuses_of(session: AsyncSession, interview_id, emails: list[str]) -> dict[str, str]:
    """The statuses of those of `emails` (lowercase) invited to the interview, by email."""
    query = select(CandidateInvite.email, CandidateInvite.status).where(
        CandidateInvite.interview_id == interview_id, CandidateInvite.email.in_(emails)
    )

    return dict((await session.execute(query)).all())


async def unfinished(
    session: AsyncSession, interview_id, after: uuid.UUID | None, size: int
) -> list[CandidateInvite]:
    """Up to `size` of the interview's invites not finished yet, by id, those after `after`."""
    query = select(CandidateInvite).where(
        CandidateInvite.interview_id == interview_id,
        CandidateInvite.status != InviteStatus.FINISHED,
    )

    if after is not None:
        query = query.where(CandidateInvite.id > after)

    query = query.order_by(CandidateInvite.id).limit(size)

    return list(await session.scalars(query))


async def get(session: AsyncSession, invite_id: uuid.UUID) -> CandidateInvite | None:
    return await session.get(CandidateInvite, invite_id)


async def get_by_token(
    session: AsyncSession, token: str
) -> tuple[CandidateInvite, Interview] | None:
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(CandidateInvite.token == token)
    )

    row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def remove(session: AsyncSession, invite: CandidateInvite, company_id) -> str | None:
    """Deletes the invite (its link stops working) and tells the other services, which forget the
    candidate too: the company's notifications about them, the ATS's record of them. Returns its
    status as it was deleted."""
    await guests.announce_deleted(session, CandidateInvite.id == invite.id)
    # Erased again after a restore from a backup (services/removal_replay.py).
    await session.execute(
        insert(RemovedInvite)
        .values(invite_id=invite.id, company_id=company_id)
        .on_conflict_do_nothing()
    )
    removed = await session.scalar(
        delete(CandidateInvite)
        .where(CandidateInvite.id == invite.id)
        .returning(CandidateInvite.status)
    )
    outbox.add(
        session,
        CANDIDATE_REMOVED,
        {
            "company_id": str(company_id),
            "interview_id": str(invite.interview_id),
            "candidate_invite_id": str(invite.id),
            "email": invite.email,
        },
    )

    return removed


async def change(session: AsyncSession, invite_id: uuid.UUID, values: dict, statuses) -> bool:
    """Writes an owner or admin's changes to the candidate (`name`, `extra_time`) in one
    statement, all or none: only while the invite's status is one of `statuses`, so a candidate
    who started, or was deleted, since it was read keeps theirs. Whether it was written."""
    query = (
        update(CandidateInvite)
        .where(CandidateInvite.id == invite_id, CandidateInvite.status.in_(statuses))
        .values(**values)
    )

    written = (await session.execute(query)).rowcount

    return written > 0


async def company_ids_for(session: AsyncSession, email: str) -> list[str]:
    """The companies with an invite for the address, whatever its case."""
    query = (
        select(Interview.company_id)
        .join(CandidateInvite, CandidateInvite.interview_id == Interview.id)
        .where(CandidateInvite.email == email.strip().lower())
        .distinct()
    )

    return [str(company_id) for company_id in await session.scalars(query)]
