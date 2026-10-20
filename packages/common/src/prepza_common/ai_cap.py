"""The daily AI spend cap for unpaid companies and people without a company (the
AI_SPEND_UNPAID_DAY limit): billing adds each of their calls' cost as it stores it, and the
services refuse their AI calls (503) once today's (UTC) total reaches it, until midnight UTC."""

import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from prepza_common.ai_constants import (
    AI_PAUSED_TODAY,
    MICRO,
    UNPAID_SPEND_ALERT_SHARE,
    UNPAID_SPEND_KEY,
    UNPAID_SPEND_KEY_SECONDS,
)
from prepza_common.limits import limit as limit_value
from prepza_common.limits import record_hit
from prepza_common.rate_limit import until_tomorrow

logger = logging.getLogger(__name__)

CAP = "AI_SPEND_UNPAID_DAY"


def today_key() -> str:
    return f"{UNPAID_SPEND_KEY}:{datetime.now(UTC).date().isoformat()}"


async def spent_today(redis) -> float:
    """Unpaid AI spend today (UTC), in USD."""
    return int(await redis.get(today_key()) or 0) / MICRO


async def refuse_if_capped(
    redis, company_id: object | None = None, user_id: str | None = None
) -> None:
    """For an AI call made for an unpaid company or someone without one: refused (503) once
    today's unpaid spend reached the cap. With Redis down, not refused."""
    try:
        cap = await limit_value(redis, CAP)
        spent = await spent_today(redis)
    except Exception:
        logger.warning("Couldn't read today's unpaid AI spend; not capped", exc_info=True)

        return

    if spent < cap:
        return

    await record_hit(CAP, company_id=company_id, user_id=user_id)

    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE, AI_PAUSED_TODAY, headers=until_tomorrow()
    )


async def add_unpaid(redis, cost_usd: float) -> None:
    """Adds an unpaid call's cost to today's total. Crossing UNPAID_SPEND_ALERT_SHARE of the cap,
    and the cap, each logs once (the alerts)."""
    key = today_key()

    async with redis.pipeline(transaction=True) as pipe:
        pipe.incrby(key, round(cost_usd * MICRO))
        pipe.expire(key, UNPAID_SPEND_KEY_SECONDS)
        total, _ = await pipe.execute()

    cap = await limit_value(redis, CAP) * MICRO
    before = total - round(cost_usd * MICRO)

    if before < cap * UNPAID_SPEND_ALERT_SHARE <= total:
        logger.warning("Unpaid AI spend near the daily cap: $%.2f", total / MICRO)

    if before < cap <= total:
        logger.error("Unpaid AI spend reached the daily cap: $%.2f", total / MICRO)
