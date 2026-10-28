"""Who and what a company's action log names, looked up when it's read, so it never keeps a
person's email: its members' emails and what its actions were about."""

from sqlalchemy import select

from companies.core.db import Session
from companies.models.companies import Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite


async def member_emails(company_id, user_ids: list[str]) -> dict[str, str]:
    """The emails the company's members with those user ids were invited at."""
    if not user_ids:
        return {}

    query = select(Member.user_id, Member.invited_email).where(
        Member.company_id == company_id, Member.user_id.in_(user_ids)
    )

    async with Session() as session:
        return {user_id: email for user_id, email in await session.execute(query)}


async def target_names(company_id, ids: list) -> dict:
    """What the company's actions were about, by id: a candidate invite's email, an interview's
    title, or a member's email. Ids of anything gone, or of anything else, are left out."""
    if not ids:
        return {}

    queries = [
        select(CandidateInvite.id, CandidateInvite.email)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(Interview.company_id == company_id, CandidateInvite.id.in_(ids)),
        select(Interview.id, Interview.title).where(
            Interview.company_id == company_id, Interview.id.in_(ids)
        ),
        select(Member.id, Member.invited_email).where(
            Member.company_id == company_id, Member.id.in_(ids)
        ),
    ]
    found = {}

    async with Session() as session:
        for query in queries:
            found |= {id: name for id, name in await session.execute(query) if name}

    return found
