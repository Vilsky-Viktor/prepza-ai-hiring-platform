"""The admin zone's stats: each service counts its own records, all time or in one UTC year or
month, and answers in one shape, which the stats tab puts together."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# The period asked for: a year ("2026") or a month ("2026-10"); None for all time.
Period = Annotated[str | None, Query(pattern=r"^\d{4}(-(0[1-9]|1[0-2]))?$")]


class StatsOut(BaseModel):
    counts: dict[str, int]
    # What was paid, in minor units by currency, for the service that takes payments.
    paid: dict[str, int] | None = None


def period_range(period: str) -> tuple[datetime, datetime]:
    """The first moment of the UTC year "2026" or month "2026-10", and of the one after it."""
    year, _, month = period.partition("-")

    if not month:
        return datetime(int(year), 1, 1, tzinfo=UTC), datetime(int(year) + 1, 1, 1, tzinfo=UTC)

    number = int(month)
    start = datetime(int(year), number, 1, tzinfo=UTC)
    end = datetime(int(year) + number // 12, number % 12 + 1, 1, tzinfo=UTC)

    return start, end


async def counted(
    session: AsyncSession, value: ColumnElement, at: ColumnElement, period: str | None, *where
) -> int:
    """`value` (a count or a sum) over the rows matching `where`: every one, or those whose `at`
    is in `period` (a year or a month)."""
    if period:
        start, end = period_range(period)
        where = (*where, at >= start, at < end)

    return int(await session.scalar(select(func.coalesce(value, 0)).where(*where)))
