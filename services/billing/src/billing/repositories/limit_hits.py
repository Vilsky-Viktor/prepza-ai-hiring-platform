"""The limit hits the AI costs tab and Controls show."""

from datetime import datetime

from prepza_common.db.stats import period_range
from sqlalchemy import func, select

from billing.core.db import Session
from billing.models.usage import LimitHit

HITS = func.count(LimitHit.id)


def since(period: str | None) -> list:
    if not period:
        return []

    start, end = period_range(period)

    return [LimitHit.occurred_at >= start, LimitHit.occurred_at < end]


async def counts(where: list) -> list:
    """Each limit's hits, most first, with its kind and scope."""
    query = (
        select(LimitHit.limit, LimitHit.kind, func.max(LimitHit.scope), HITS)
        .where(*where)
        .group_by(LimitHit.limit, LimitHit.kind)
        .order_by(HITS.desc())
    )

    async with Session() as session:
        return list((await session.execute(query)).all())


async def hitters(column, where: list, top: int) -> list:
    """(limit, company or user, hits): each limit's `top` that hit it most, most first."""
    rank = func.row_number().over(partition_by=LimitHit.limit, order_by=(HITS.desc(), column))
    counted = (
        select(LimitHit.limit, column.label("key"), HITS.label("hits"), rank.label("rank"))
        .where(column.is_not(None), *where)
        .group_by(LimitHit.limit, column)
        .subquery()
    )
    query = (
        select(counted.c.limit, counted.c.key, counted.c.hits)
        .where(counted.c.rank <= top)
        .order_by(counted.c.hits.desc(), counted.c.key)
    )

    async with Session() as session:
        return list((await session.execute(query)).all())


async def counts_since(start: datetime) -> dict[str, int]:
    query = select(LimitHit.limit, HITS).where(LimitHit.occurred_at >= start)

    async with Session() as session:
        rows = await session.execute(query.group_by(LimitHit.limit))

        return {name: hits for name, hits in rows.all()}
