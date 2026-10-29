from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from companies.constants.invites import InviteStatus
from companies.constants.roles import Role
from companies.models.audit import AuditEvent
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import guests, interview_notes


async def memberships(session: AsyncSession, user_id: str) -> list[tuple[Member, Company, int]]:
    """The user's memberships, each with its company and that company's number of owners."""
    owner = aliased(Member)
    owners = (
        select(func.count())
        .where(owner.company_id == Company.id, owner.role == Role.OWNER)
        .correlate(Company)
        .scalar_subquery()
    )
    query = (
        select(Member, Company, owners)
        .join(Company, Company.id == Member.company_id)
        .where(Member.user_id == user_id)
    )

    return [tuple(row) for row in await session.execute(query)]


async def owned(session: AsyncSession, user_id: str) -> list[tuple[Company, bool]]:
    """The companies the user owns, each with whether anyone else has joined it."""
    other = aliased(Member)
    shared = (
        select(other.id)
        .where(other.company_id == Company.id, other.user_id.is_not(None), other.user_id != user_id)
        .exists()
    )
    query = (
        select(Company, shared)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id == user_id, Member.role == Role.OWNER)
        .order_by(Company.name)
    )

    return [tuple(row) for row in await session.execute(query)]


async def remove_member(session: AsyncSession, member_id) -> None:
    await session.execute(delete(Member).where(Member.id == member_id))


async def unfinished_invites(
    session: AsyncSession, user_id: str, email: str
) -> list[CandidateInvite]:
    """The invites the user was sent or accepted that they haven't finished."""
    query = select(CandidateInvite).where(
        or_(CandidateInvite.user_id == user_id, CandidateInvite.email == email.lower()),
        CandidateInvite.status != InviteStatus.FINISHED,
    )

    return list(await session.scalars(query))


async def candidate_invites(
    session: AsyncSession, user_id: str, email: str
) -> list[tuple[CandidateInvite, UUID]]:
    """Every invite the person was sent or started, each with its company. An empty
    (unverified) email matches by id only."""
    matched = [CandidateInvite.user_id == user_id]

    if email:
        matched.append(CandidateInvite.email == email.lower())

    query = (
        select(CandidateInvite, Interview.company_id)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(or_(*matched))
    )

    return [tuple(row) for row in await session.execute(query)]


async def blanked_invites(session: AsyncSession, limit: int) -> list:
    """Up to `limit` ids of invites a deleted account once left, blanked (status deleted)."""
    query = (
        select(CandidateInvite.id)
        .where(CandidateInvite.status == InviteStatus.DELETED)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def forget_member_invites(session: AsyncSession, email: str) -> None:
    """Team invites to the address not yet accepted: the person who deleted their account is
    no longer invited (their email goes with them). An empty (unverified) email matches none."""
    await session.execute(
        delete(Member).where(
            Member.user_id.is_(None), func.lower(Member.invited_email) == email.lower()
        )
    )


async def forget_verification_email(session: AsyncSession, email: str) -> None:
    """A company keeps its verification, but not the email of a person who deleted their account
    as its proof."""
    await session.execute(
        update(Company)
        .where(func.lower(Company.verification_email) == email.lower())
        .values(verification_email=None)
    )


async def export(session: AsyncSession, user_id: str, email: str) -> dict:
    companies = await session.execute(
        select(Company.name, Member.role, Member.created_at)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id == user_id)
    )
    pending = await session.execute(
        select(Company.name, Member.role, Member.created_at)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id.is_(None), func.lower(Member.invited_email) == email.lower())
    )
    invites = await session.execute(
        select(
            Interview.title,
            CandidateInvite.name,
            CandidateInvite.status,
            CandidateInvite.created_at,
            CandidateInvite.pledged_at,
            CandidateInvite.extra_time,
            CandidateInvite.started_at,
            CandidateInvite.finished_at,
            CandidateInvite.undelivered_at,
        )
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(or_(CandidateInvite.user_id == user_id, CandidateInvite.email == email.lower()))
    )
    verifications = await session.execute(
        select(Company.name, Company.verification_email).where(
            func.lower(Company.verification_email) == email.lower()
        )
    )
    decisions = await session.execute(
        select(
            Company.name,
            AuditEvent.action,
            AuditEvent.target_id,
            AuditEvent.via,
            AuditEvent.created_at,
        )
        .join(Company, Company.id == AuditEvent.company_id)
        .where(AuditEvent.user_id == user_id)
        .order_by(AuditEvent.created_at)
    )
    notes = await interview_notes.authored(session, user_id)

    return {
        "company_memberships": [
            {"company": name, "role": role, "since": since} for name, role, since in companies
        ],
        # Invitations to join a team, not accepted yet.
        "company_invitations": [
            {"company": name, "role": role, "invited_at": at} for name, role, at in pending
        ],
        "interview_invites": [
            {
                "interview": title,
                "name": name,
                "status": status,
                "invited_at": at,
                # When they confirmed they'd answer on their own.
                "pledged_at": pledged,
                # Extra seconds a question the company gave them.
                "extra_time": extra,
                "started_at": started,
                "finished_at": finished,
                # When their invite email couldn't be delivered.
                "undelivered_at": undelivered,
            }
            for title, name, status, at, pledged, extra, started, finished, undelivered in invites
        ],
        "company_verifications": [
            {"company": name, "verification_email": proof} for name, proof in verifications
        ],
        "company_decisions": [
            {"company": name, "action": action, "target_id": target_id, "via": via, "at": at}
            for name, action, target_id, via, at in decisions
        ],
        # The notes they wrote on their companies' interviews.
        "interview_notes": [
            {
                "company": name,
                "interview": title,
                "text": text,
                "written_at": at,
                "edited_at": edited,
            }
            for name, title, text, at, edited in notes
        ],
    }


async def expired_invites(session: AsyncSession, before: datetime, limit: int) -> list[tuple]:
    """(id, interview id, email, status, hold key) of up to `limit` invites last sent before `before`:
    kept CANDIDATE_RETENTION_DAYS after the latest send, as the privacy policy says, so sending
    one again keeps its results longer."""
    query = (
        select(
            CandidateInvite.id,
            CandidateInvite.interview_id,
            CandidateInvite.email,
            CandidateInvite.status,
            CandidateInvite.hold_key,
        )
        .where(CandidateInvite.sent_at < before)
        .order_by(CandidateInvite.sent_at)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def delete_invites(session: AsyncSession, invite_ids: list) -> None:
    """Deletes the invites, announcing the guests among them."""
    if not invite_ids:
        return

    await guests.announce_deleted(session, CandidateInvite.id.in_(invite_ids))
    await session.execute(delete(CandidateInvite).where(CandidateInvite.id.in_(invite_ids)))
