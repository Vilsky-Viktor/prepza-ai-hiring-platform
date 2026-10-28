"""The AI costs tab's sums over ai_usage, all time or in one UTC year or month."""

from datetime import datetime

from prepza_common.ai.ai_constants import Category
from prepza_common.db.stats import period_range
from sqlalchemy import ColumnElement, Float, String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from billing.constants.usage import TRANSCRIPTION
from billing.models.usage import AiUsage

# Summed exactly (numeric), then read as a float.
SPEND = func.coalesce(cast(func.sum(AiUsage.cost), Float), 0.0)
CALLS = func.count(AiUsage.id)
TOKENS = (
    func.coalesce(func.sum(AiUsage.input_tokens), 0),
    func.coalesce(func.sum(AiUsage.cached_input_tokens), 0),
    func.coalesce(func.sum(AiUsage.output_tokens), 0),
)
UNPAID = (Category.UNPAID, Category.NO_COMPANY)


def in_period(period: str | None) -> list[ColumnElement]:
    if not period:
        return []

    start, end = period_range(period)

    return [AiUsage.occurred_at >= start, AiUsage.occurred_at < end]


def between(start: datetime, end: datetime) -> list[ColumnElement]:
    return [AiUsage.occurred_at >= start, AiUsage.occurred_at < end]


def spend_where(*where) -> ColumnElement:
    return func.coalesce(cast(func.sum(AiUsage.cost).filter(*where), Float), 0.0)


async def rows(session: AsyncSession, query) -> list:
    return list((await session.execute(query)).all())


async def totals(session: AsyncSession, where: list[ColumnElement]):
    [found] = await rows(session, select(SPEND, CALLS, *TOKENS).where(*where))

    return found


async def by_category(session: AsyncSession, where: list[ColumnElement]) -> list:
    return await rows(
        session, select(AiUsage.category, SPEND, CALLS).where(*where).group_by(AiUsage.category)
    )


async def by_action(session: AsyncSession, where: list[ColumnElement]) -> list:
    """Each action's spend, calls and units: minutes for transcription, otherwise what each was
    for (a generation, a message), or the call itself when it names none."""
    subject = func.coalesce(AiUsage.subject_id, cast(AiUsage.id, String))
    units = func.count(func.distinct(subject))
    minutes = func.coalesce(func.sum(AiUsage.audio_seconds), 0.0) / 60
    query = (
        select(
            AiUsage.action,
            SPEND,
            CALLS,
            units,
            minutes,
            spend_where(AiUsage.category == Category.PAID),
            spend_where(AiUsage.category.in_(UNPAID)),
        )
        .where(*where)
        .group_by(AiUsage.action)
        .order_by(SPEND.desc())
    )

    return [
        (action, spend, calls, used_minutes if action == TRANSCRIPTION else count, paid, unpaid)
        for action, spend, calls, count, used_minutes, paid, unpaid in await rows(session, query)
    ]


async def by_model(session: AsyncSession, where: list[ColumnElement]) -> list:
    return await rows(
        session,
        select(AiUsage.model, SPEND, CALLS, *TOKENS)
        .where(*where)
        .group_by(AiUsage.model)
        .order_by(SPEND.desc()),
    )


async def top(session: AsyncSession, column, where: list[ColumnElement], count: int) -> list:
    """The `count` companies or users (`column`) that cost most."""
    return await rows(
        session,
        select(column, SPEND, CALLS)
        .where(column.is_not(None), *where)
        .group_by(column)
        .order_by(SPEND.desc())
        .limit(count),
    )


async def by_day(session: AsyncSession, where: list[ColumnElement], unit: str) -> list:
    """Spend per UTC day or month (`unit`), oldest first."""
    day = func.date_trunc(unit, func.timezone("UTC", AiUsage.occurred_at))

    return await rows(session, select(day, SPEND).where(*where).group_by(day).order_by(day))


async def spend_of(session: AsyncSession, column, value: str, start: datetime, end: datetime):
    [found] = await rows(session, select(SPEND, CALLS).where(column == value, *between(start, end)))

    return found
