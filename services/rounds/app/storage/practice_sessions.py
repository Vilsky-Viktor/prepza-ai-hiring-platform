import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import selectinload

from app.models.sessions import Session
from app.storage.db import Session as Db


def _practice(user_id: str, template_id: uuid.UUID):
    return (
        Session.user_id == user_id,
        Session.interview_set_id == template_id,
        Session.practice.is_(True),
    )


async def practiced(user_id: str, template_id: uuid.UUID) -> bool:
    """Whether the talent took a practice round on the template before."""
    async with Db() as session:
        return bool(await session.scalar(select(exists().where(*_practice(user_id, template_id)))))


async def practice_rounds(
    user_id: str, template_id: uuid.UUID, offset: int, limit: int
) -> list[Session]:
    """The sections, with answers, of the talent's practice rounds on the template, a page of
    rounds at a time, newest first."""
    rounds = (
        select(Session.candidate_invite_id)
        .where(*_practice(user_id, template_id))
        .group_by(Session.candidate_invite_id)
        .order_by(func.min(Session.started_at).desc(), Session.candidate_invite_id)
        .offset(offset)
        .limit(limit)
    )
    query = (
        select(Session)
        .where(Session.candidate_invite_id.in_(rounds))
        .options(selectinload(Session.answers))
    )

    async with Db() as session:
        return list(await session.scalars(query))


async def latest_round_sections(user_id: str) -> list[tuple[uuid.UUID, str]]:
    """The template and status of each section of the talent's latest practice round on every
    template they practiced."""
    latest = (
        select(Session.candidate_invite_id)
        .where(Session.user_id == user_id, Session.practice.is_(True))
        .group_by(Session.interview_set_id, Session.candidate_invite_id)
        .order_by(Session.interview_set_id, func.min(Session.started_at).desc())
        .ext(distinct_on(Session.interview_set_id))
    )
    query = select(Session.interview_set_id, Session.status).where(
        Session.candidate_invite_id.in_(latest)
    )

    async with Db() as session:
        return [(row.interview_set_id, row.status) for row in await session.execute(query)]
