from datetime import datetime

from sqlalchemy import Text, delete, func, literal, or_, select, update
from sqlalchemy.orm import aliased

from app.constants.invites import InviteStatus
from app.constants.roles import Role
from app.models.audit import AuditEvent
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.storage import guests
from app.storage.db import Session


async def memberships(user_id: str) -> list[tuple[Member, Company, int]]:
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

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def owned(user_id: str) -> list[tuple[Company, bool]]:
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

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def remove_member(member_id) -> None:
    async with Session() as session:
        await session.execute(delete(Member).where(Member.id == member_id))
        await session.commit()


async def unfinished_invites(user_id: str, email: str) -> list[CandidateInvite]:
    """The invites the user was sent or accepted that they haven't finished."""
    query = select(CandidateInvite).where(
        or_(CandidateInvite.user_id == user_id, CandidateInvite.email == email.lower()),
        CandidateInvite.status != InviteStatus.FINISHED,
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def forget_candidate(user_id: str, email: str) -> None:
    """Keeps the company's invite row, marked deleted, without the candidate's email, name or a
    usable link. The email becomes unique per invite, as an interview can't hold it twice."""
    async with Session() as session:
        await session.execute(
            update(CandidateInvite)
            .where(or_(CandidateInvite.user_id == user_id, CandidateInvite.email == email.lower()))
            .values(
                status=InviteStatus.DELETED,
                email=literal("deleted-") + func.cast(CandidateInvite.id, Text()),
                name=None,
                token=func.md5(func.random().cast(Text()) + func.cast(CandidateInvite.id, Text())),
                user_id=None,
            )
        )
        await session.commit()


async def forget_verification_email(email: str) -> None:
    """A company keeps its verification, but not the email of a person who deleted their account
    as its proof."""
    async with Session() as session:
        await session.execute(
            update(Company)
            .where(func.lower(Company.verification_email) == email.lower())
            .values(verification_email=None)
        )
        await session.commit()


async def export(user_id: str, email: str) -> dict:
    async with Session() as session:
        companies = await session.execute(
            select(Company.name, Member.role, Member.created_at)
            .join(Member, Member.company_id == Company.id)
            .where(Member.user_id == user_id)
        )
        invites = await session.execute(
            select(
                Interview.title,
                CandidateInvite.name,
                CandidateInvite.status,
                CandidateInvite.created_at,
                CandidateInvite.pledged_at,
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

        return {
            "company_memberships": [
                {"company": name, "role": role, "since": since} for name, role, since in companies
            ],
            "interview_invites": [
                {
                    "interview": title,
                    "name": name,
                    "status": status,
                    "invited_at": at,
                    # When they confirmed they'd answer on their own.
                    "pledged_at": pledged,
                }
                for title, name, status, at, pledged in invites
            ],
            "company_verifications": [
                {"company": name, "verification_email": proof} for name, proof in verifications
            ],
            "company_decisions": [
                {"company": name, "action": action, "target_id": target_id, "via": via, "at": at}
                for name, action, target_id, via, at in decisions
            ],
        }


async def expired_invites(before: datetime, limit: int) -> list[tuple]:
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

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def delete_invites(invite_ids: list) -> None:
    if not invite_ids:
        return

    async with Session() as session:
        await guests.announce_deleted(session, CandidateInvite.id.in_(invite_ids))
        await session.execute(delete(CandidateInvite).where(CandidateInvite.id.in_(invite_ids)))
        await session.commit()
