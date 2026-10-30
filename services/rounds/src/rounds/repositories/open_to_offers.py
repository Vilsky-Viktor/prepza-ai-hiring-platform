import uuid
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.constants.rounds import RoundStatus
from rounds.models.open_to_offers import OfferConsent, OpenToOffers
from rounds.models.sessions import Session


async def get(session: AsyncSession, user_id: str) -> OpenToOffers | None:
    return await session.get(OpenToOffers, user_id)


async def save(
    session: AsyncSession, user_id: str, name: str | None, linkedin_url: str, now: datetime
) -> None:
    """Lists the person (again) with this name and profile, the lapse counting from `now`."""
    values = {"name": name, "linkedin_url": linkedin_url, "opened_at": now}
    await session.execute(
        insert(OpenToOffers)
        .values(user_id=user_id, **values)
        .on_conflict_do_update(index_elements=[OpenToOffers.user_id], set_=values)
    )


async def close(session: AsyncSession, user_ids: list[str]) -> list[str]:
    """Takes these people off every Discover tab; gives those who were on it."""
    closed = await session.scalars(
        delete(OpenToOffers)
        .where(OpenToOffers.user_id.in_(user_ids))
        .returning(OpenToOffers.user_id)
    )

    return list(closed)


async def lapsed(session: AsyncSession, before: datetime, limit: int) -> list[str]:
    """Up to `limit` people last turned on before `before`, locked for closing them."""
    found = await session.scalars(
        select(OpenToOffers.user_id)
        .where(OpenToOffers.opened_at < before)
        .order_by(OpenToOffers.opened_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )

    return list(found)


async def log(session: AsyncSession, user_ids: list[str], granted: bool, version: str | None):
    """One consent log entry per person: what they agreed to (or that it ended) and when."""
    session.add_all(
        OfferConsent(user_id=user_id, granted=granted, text_version=version) for user_id in user_ids
    )


async def consents(session: AsyncSession, user_id: str) -> list[OfferConsent]:
    found = await session.scalars(
        select(OfferConsent)
        .where(OfferConsent.user_id == user_id)
        .order_by(OfferConsent.created_at)
    )

    return list(found)


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """The person's opt-in and its consent log; safe to repeat."""
    await session.execute(delete(OpenToOffers).where(OpenToOffers.user_id == user_id))
    await session.execute(delete(OfferConsent).where(OfferConsent.user_id == user_id))


def _latest_results(topic_ids: list[uuid.UUID]):
    """Each listed person's latest finished, timed practice section on each of these topics."""
    return (
        select(
            Session.user_id,
            Session.topic_title,
            Session.final_score,
            Session.finished_at,
        )
        .join(OpenToOffers, OpenToOffers.user_id == Session.user_id)
        .where(
            Session.practice.is_(True),
            Session.status == RoundStatus.FINISHED,
            Session.final_score.is_not(None),
            Session.question_seconds.is_not(None),
            Session.topic_id.in_(topic_ids),
        )
        .order_by(Session.user_id, Session.topic_id, Session.finished_at.desc())
        .distinct(Session.user_id, Session.topic_id)
        .subquery()
    )


async def matches(
    session: AsyncSession, topic_ids: list[uuid.UUID], offset: int, limit: int
) -> tuple[list[OpenToOffers], list[Row]]:
    """A page of the listed people with results on these topics, whoever practised last first
    (a fixed order, never a ranking), and their results on them, newest first."""
    latest = _latest_results(topic_ids)
    page = (
        select(latest.c.user_id)
        .group_by(latest.c.user_id)
        .order_by(func.max(latest.c.finished_at).desc(), latest.c.user_id)
        .offset(offset)
        .limit(limit)
    )
    user_ids = list(await session.scalars(page))

    if not user_ids:
        return [], []

    people = await session.scalars(select(OpenToOffers).where(OpenToOffers.user_id.in_(user_ids)))
    results = await session.execute(
        select(latest)
        .where(latest.c.user_id.in_(user_ids))
        .order_by(latest.c.finished_at.desc(), latest.c.topic_title)
    )
    order = {user_id: index for index, user_id in enumerate(user_ids)}

    return sorted(people, key=lambda person: order[person.user_id]), list(results)
