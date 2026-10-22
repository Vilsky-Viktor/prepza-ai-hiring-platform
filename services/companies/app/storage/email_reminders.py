import uuid
from datetime import datetime

from sqlalchemy import exists, select, union
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


def idle(ready_after: datetime, ready_before: datetime) -> list:
    """Interviews that got their questions between those times, nobody was invited to, and
    that aren't marked hired."""
    invited = exists().where(CandidateInvite.interview_id == Interview.id)

    return [
        Interview.ready_at > ready_after,
        Interview.ready_at <= ready_before,
        Interview.hired.is_(False),
        ~invited,
    ]


def generating(started_after: datetime, started_before: datetime) -> list:
    """Interviews started between those times still waiting for their questions: their
    generation may be waiting for its topics' review."""
    return [
        Interview.created_at > started_after,
        Interview.created_at <= started_before,
        Interview.generation_id.is_not(None),
        Interview.set_id.is_(None),
        Interview.generation_failed.is_(False),
    ]


async def waiting_company_ids(
    ready: tuple[datetime, datetime],
    started: tuple[datetime, datetime],
    after: uuid.UUID | None,
    limit: int,
) -> list[uuid.UUID]:
    """The companies with an interview nobody was invited to (ready within `ready`) or one
    still generating (started within `started`), in order: up to `limit` after `after`."""
    later = [Interview.company_id > after] if after else []
    query = union(
        select(Interview.company_id).where(*idle(*ready), *later),
        select(Interview.company_id).where(*generating(*started), *later),
    ).subquery()

    async with Session() as session:
        rows = await session.scalars(
            select(query.c.company_id).order_by(query.c.company_id).limit(limit)
        )

        return list(rows)


async def waiting_of(
    ready: tuple[datetime, datetime], started: tuple[datetime, datetime], company_ids: list
) -> tuple[list[Interview], list[Interview]]:
    """Those companies' interviews nobody was invited to and those still generating."""
    of_them = Interview.company_id.in_(company_ids)

    async with Session() as session:
        without = await session.scalars(select(Interview).where(*idle(*ready), of_them))
        being = await session.scalars(select(Interview).where(*generating(*started), of_them))

        return list(without), list(being)


async def member_ids(after: str, limit: int, editors_only: bool) -> list[str]:
    """Everyone who joined a company, in any role, or with `editors_only` only its owners and
    admins, once each, in order: up to `limit` after `after`."""
    query = select(Member.user_id).where(Member.user_id > after)

    if editors_only:
        query = query.where(Member.role.in_(EDITORS))

    async with Session() as session:
        rows = await session.scalars(query.distinct().order_by(Member.user_id).limit(limit))

        return list(rows)
