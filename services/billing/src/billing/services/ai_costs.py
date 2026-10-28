"""The admin zone's AI costs tab: what AI cost in a period and why, put together from ai_usage,
Redis (today's unpaid spend) and the companies' and accounts' names. The page only shows it."""

import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.ai.ai_cap import CAP, spent_today
from prepza_common.limits.limits import limit

from billing.constants.usage import SPEND_DAYS, TOP_SPENDERS
from billing.core.db import Session
from billing.integrations import names
from billing.integrations.redis import get_redis
from billing.models.usage import AiUsage
from billing.repositories import ai_costs
from billing.schemas.ai_costs import (
    ActionOut,
    AiCostsOut,
    AiSpendOut,
    CategoryOut,
    DayOut,
    ModelOut,
    MonthOut,
    SpenderOut,
    TotalsOut,
    UnpaidTodayOut,
)


def share(part: float, whole: float) -> float:
    return part / whole if whole else 0.0


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False

    return True


async def spenders(found: list, named) -> list[SpenderOut]:
    """The top spenders read (`found`), named by `named`."""
    known = await named([key for key, _, _ in found])

    return [
        SpenderOut(id=key, name=known.get(key), spend=spend, calls=calls)
        for key, spend, calls in found
    ]


async def company_names(ids: list[str]) -> dict[str, str]:
    return await names.company_names([key for key in ids if is_uuid(key)])


async def month_out() -> MonthOut:
    month = datetime.now(UTC).strftime("%Y-%m")

    async with Session() as session:
        spend, _, _, _, _ = await ai_costs.totals(session, ai_costs.in_period(month))

    # 0: no budget, the month's spend alone.
    budget = await limit(get_redis(), "MONTHLY_BUDGET")

    return MonthOut(spend=spend, budget=budget, share=share(spend, budget))


async def unpaid_today() -> UnpaidTodayOut:
    redis = get_redis()
    spend = await spent_today(redis)
    cap = await limit(redis, CAP)

    return UnpaidTodayOut(spend=spend, cap=cap, share=share(spend, cap))


async def ai_costs_out(period: str | None) -> AiCostsOut:
    where = ai_costs.in_period(period)
    by_month = not period or len(period) == 4

    async with Session() as session:
        spend, calls, input_tokens, cached, output = await ai_costs.totals(session, where)
        categories = await ai_costs.by_category(session, where)
        actions = await ai_costs.by_action(session, where)
        models = await ai_costs.by_model(session, where)
        companies = await ai_costs.top(session, AiUsage.company_id, where, TOP_SPENDERS)
        users = await ai_costs.top(session, AiUsage.user_id, where, TOP_SPENDERS)
        days = await ai_costs.by_day(session, where, "month" if by_month else "day")

    tokens = {"input_tokens": input_tokens, "cached_input_tokens": cached}

    return AiCostsOut(
        totals=TotalsOut(spend=spend, calls=calls, output_tokens=output, **tokens),
        month=await month_out(),
        unpaid_today=await unpaid_today(),
        categories=[
            CategoryOut(category=category, spend=part, calls=count, share=share(part, spend))
            for category, part, count in categories
        ],
        actions=[
            ActionOut(
                action=action,
                spend=part,
                calls=count,
                units=units,
                unit_cost=share(part, units),
                paid_spend=paid,
                unpaid_spend=unpaid,
            )
            for action, part, count, units, paid, unpaid in actions
        ],
        models=[
            ModelOut(
                model=model,
                spend=part,
                calls=count,
                input_tokens=read,
                cached_input_tokens=hit,
                output_tokens=written,
                cached_share=share(hit, read),
            )
            for model, part, count, read, hit, written in models
        ],
        companies=await spenders(companies, company_names),
        users=await spenders(users, names.user_emails),
        by_month=by_month,
        days=[DayOut(day=day.date(), spend=part) for day, part in days],
    )


async def spend_out(company_id: str | None, user_id: str | None) -> AiSpendOut:
    """A company's or a user's AI spend over the last SPEND_DAYS days."""
    end = datetime.now(UTC)
    start = end - timedelta(days=SPEND_DAYS)
    column, value = (AiUsage.company_id, company_id) if company_id else (AiUsage.user_id, user_id)
    async with Session() as session:
        spend, calls = await ai_costs.spend_of(session, column, value, start, end)

    return AiSpendOut(spend=spend, calls=calls, days=SPEND_DAYS)
