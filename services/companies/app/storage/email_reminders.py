from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload

from app.constants.roles import EDITORS
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.storage.db import Session


async def with_members(company_ids: list) -> list[Company]:
    """The companies of those ids that still exist, with their members."""
    if not company_ids:
        return []

    query = (
        select(Company).where(Company.id.in_(company_ids)).options(selectinload(Company.members))
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def without_candidates(ready_after: datetime, ready_before: datetime) -> list[Interview]:
    """Interviews that got their questions between those times, nobody was invited to, and
    that aren't marked hired."""
    invited = exists().where(CandidateInvite.interview_id == Interview.id)
    query = select(Interview).where(
        Interview.ready_at > ready_after,
        Interview.ready_at <= ready_before,
        Interview.hired.is_(False),
        ~invited,
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def being_generated(started_after: datetime, started_before: datetime) -> list[Interview]:
    """Interviews started between those times still waiting for their questions: their
    generation may be waiting for its topics' review."""
    query = select(Interview).where(
        Interview.created_at > started_after,
        Interview.created_at <= started_before,
        Interview.generation_id.is_not(None),
        Interview.set_id.is_(None),
        Interview.generation_failed.is_(False),
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def editor_ids(after: str, limit: int) -> list[str]:
    """Everyone who owns or runs a company (a joined owner or admin), once each, in order: up to
    `limit` after `after`."""
    async with Session() as session:
        rows = await session.scalars(
            select(Member.user_id)
            .where(Member.role.in_(EDITORS), Member.user_id > after)
            .distinct()
            .order_by(Member.user_id)
            .limit(limit)
        )

        return list(rows)
