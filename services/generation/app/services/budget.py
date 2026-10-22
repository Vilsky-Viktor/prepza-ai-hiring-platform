from datetime import UTC, datetime

from fastapi import HTTPException, status
from prepza_common import error_codes
from prepza_common.i18n import CodedError
from prepza_common.limit_list import LIMITS
from prepza_common.limit_schemas import BudgetOut
from prepza_common.limits import limit, record_hit
from prepza_common.rate_limit import until_tomorrow

from app.constants.generation import BUDGET_KEY, BUDGET_KEY_SECONDS, GENERATIONS_PAUSED
from app.constants.quality import VERIFY_BUDGET_KEY, VERIFY_PAUSED
from app.integrations.redis import get_redis

# The shared daily budgets and their counters.
BUDGETS = {"DAILY_GENERATION_LIMIT": BUDGET_KEY, "DAILY_VERIFY_LIMIT": VERIFY_BUDGET_KEY}


def day_key(key: str) -> str:
    return f"{key}:{datetime.now(UTC).date().isoformat()}"


async def count_today(key: str) -> int:
    """Counts one use under `key` for today (UTC days); today's count so far."""
    async with get_redis().pipeline(transaction=True) as pipe:
        pipe.incr(day_key(key))
        pipe.expire(day_key(key), BUDGET_KEY_SECONDS)
        count, _ = await pipe.execute()

    return count


async def use_daily_budget(paid: bool = False, company_id=None, user_id: str | None = None) -> None:
    """Counts one new generation (or regenerated question) against today's limit for everyone
    (UTC days); past it, they wait until tomorrow. A company that ever topped up isn't held to
    it, so free sign-ups can't use it up for paying ones."""
    if paid:
        return

    name = "DAILY_GENERATION_LIMIT"

    if await count_today(BUDGET_KEY) > await limit(get_redis(), name):
        await record_hit(name, company_id=company_id, user_id=user_id)

        raise CodedError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            GENERATIONS_PAUSED,
            error_codes.AI_BUDGET_USED_UP,
            headers=until_tomorrow(),
        )


async def use_verify_budget() -> None:
    """Counts one verifier job against today's limit for everyone: reports and answers can't
    drive unlimited rewrites. Past it, the library keeps the flag and sends it again later."""
    name = "DAILY_VERIFY_LIMIT"

    if await count_today(VERIFY_BUDGET_KEY) > await limit(get_redis(), name):
        await record_hit(name)

        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, VERIFY_PAUSED, headers=until_tomorrow()
        )


async def budgets() -> list[BudgetOut]:
    """How much of each shared daily budget is used today."""
    redis = get_redis()

    return [
        BudgetOut(
            name=name,
            used=int(await redis.get(day_key(key)) or 0),
            limit=await limit(redis, name),
            unit=LIMITS[name].unit,
        )
        for name, key in BUDGETS.items()
    ]
