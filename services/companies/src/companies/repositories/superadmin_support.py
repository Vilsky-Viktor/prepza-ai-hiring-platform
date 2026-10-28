"""The admin zone's support tab: what an email address or an account id leads to, and the
company each candidate and interview belongs to."""

from sqlalchemy import select

from companies.core.db import Session
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite


async def companies_of_member(email: str, limit: int) -> list[Company]:
    """Companies with an owner, admin or viewer of that address, whatever its case, newest
    first."""
    query = (
        select(Company)
        .join(Member, Member.company_id == Company.id)
        .where(Member.invited_email == email.lower())
        .order_by(Company.created_at.desc())
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def companies_of_user(user_id: str, limit: int) -> list[tuple[Company, str]]:
    """Companies the account with that id (as "copy id" gives it) is a member of, newest
    first, each with the account's role there."""
    query = (
        select(Company, Member.role)
        .join(Member, Member.company_id == Company.id)
        .where(Member.user_id == user_id)
        .order_by(Company.created_at.desc())
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def candidate(invite_id) -> tuple[CandidateInvite, Interview, Company] | None:
    """The candidate invite with its interview and company; None when it's gone."""
    query = (
        select(CandidateInvite, Interview, Company)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .join(Company, Company.id == Interview.company_id)
        .where(CandidateInvite.id == invite_id)
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def interview(interview_id) -> tuple[Interview, Company] | None:
    """The interview with its company; None when it's gone."""
    query = (
        select(Interview, Company)
        .join(Company, Company.id == Interview.company_id)
        .where(Interview.id == interview_id)
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def invites_to(email: str, limit: int) -> list[tuple[CandidateInvite, Company]]:
    """Candidates invited at that address, whatever its case, newest first, each with the
    company that invited them."""
    query = (
        select(CandidateInvite, Company)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .join(Company, Company.id == Interview.company_id)
        .where(CandidateInvite.email == email.lower())
        .order_by(CandidateInvite.created_at.desc())
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]
