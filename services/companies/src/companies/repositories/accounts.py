from datetime import datetime

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import aliased

from companies.constants.invites import InviteStatus
from companies.constants.roles import Role
from companies.core.db import Session
from companies.models.audit import AuditEvent
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import guests, invites


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
    """Every invite the person was sent or started goes, as if each company erased them: a row
    kept without their email still linked back to them (its times, grade, return address), so it
    wasn't anonymous. The other services are told (candidate.removed), and a restore's copy is
    erased again (removal_replay). An empty (unverified) email matches by id only."""
    matched = [CandidateInvite.user_id == user_id]

    if email:
        matched.append(CandidateInvite.email == email.lower())

    query = (
        select(CandidateInvite, Interview.company_id)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(or_(*matched))
    )

    async with Session() as session:
        found = [tuple(row) for row in await session.execute(query)]

    for invite, company_id in found:
        await invites.remove(invite, company_id)


async def blanked_invites(limit: int) -> list:
    """Up to `limit` ids of invites a deleted account once left, blanked (status deleted)."""
    query = (
        select(CandidateInvite.id)
        .where(CandidateInvite.status == InviteStatus.DELETED)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def forget_member_invites(email: str) -> None:
    """Team invites to the address not yet accepted: the person who deleted their account is
    no longer invited (their email goes with them). An empty (unverified) email matches none."""
    async with Session() as session:
        await session.execute(
            delete(Member).where(
                Member.user_id.is_(None), func.lower(Member.invited_email) == email.lower()
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
