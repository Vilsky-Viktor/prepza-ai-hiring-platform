from uuid import UUID

from prepza_common.ai.ai_cap import refuse_if_capped
from prepza_common.limits.limit_schemas import BudgetOut
from prepza_common.limits.limits import limit
from prepza_common.limits.rate_limit import add_spent, hit, spend
from redis.exceptions import RedisError

from app.constants.limits import ALL_MESSAGES_KEY, ALL_TOKENS_KEY, PAID_CACHE_SECONDS
from app.integrations import billing


async def company_paid(redis, company_id: UUID | None) -> bool:
    """Whether the company ever topped up, from billing at most every PAID_CACHE_SECONDS."""
    if company_id is None:
        return False

    key = f"paid:company:{company_id}"
    cached = await redis.get(key)

    if cached is not None:
        return cached in ("1", b"1")

    paid = await billing.company_paid(company_id)
    await redis.set(key, "1" if paid else "0", ex=PAID_CACHE_SECONDS)

    return paid


async def any_paid(redis, company_ids: frozenset[str]) -> bool:
    """Whether any of the user's companies topped up."""
    for company_id in company_ids:
        if await company_paid(redis, UUID(company_id)):
            return True

    return False


def budgets(user_id: str, company_id: UUID | None, paid: bool) -> list[tuple[str, str]]:
    """The spending budgets a turn counts against, as keys and limit names: the user's, their
    company's and, unless the company paid, everyone's."""
    found = [(f"spend:assistant:user:{user_id}", "TOKENS_PER_USER_DAY")]

    if company_id is not None:
        found.append((f"spend:assistant:company:{company_id}", "TOKENS_PER_COMPANY_DAY"))

    if paid:
        return found

    return [*found, (ALL_TOKENS_KEY, "TOKENS_PER_DAY")]


async def check_budgets(redis, user_id: str, company_id: UUID | None, paid: bool) -> None:
    """Refuses (429) once a budget is spent."""
    for key, name in budgets(user_id, company_id, paid):
        await spend(redis, key, 0, name, company_id=company_id, user_id=user_id)


async def check(redis, user_id: str, company_id: UUID | None) -> None:
    """Counts one message, and refuses it (429) over a message limit or a spent budget; for a
    company that never topped up (or none), also once today's AI spend cap is reached (503)."""
    paid = await company_paid(redis, company_id)
    who = {"company_id": company_id, "user_id": user_id}

    if not paid:
        await refuse_if_capped(redis, **who)

    await check_budgets(redis, user_id, company_id, paid)
    await hit(redis, f"rate:assistant:hour:{user_id}", "MESSAGES_PER_USER_HOUR", **who)
    await hit(redis, f"rate:assistant:day:{user_id}", "MESSAGES_PER_USER_DAY", **who)

    if company_id is not None:
        key = f"rate:assistant:company:{company_id}"
        await hit(redis, key, "MESSAGES_PER_COMPANY_DAY", **who)

    if not paid:
        await hit(redis, ALL_MESSAGES_KEY, "MESSAGES_PER_DAY", **who)


async def check_transcription(redis, user_id: str, company_ids: frozenset[str]) -> None:
    """Counts one voice message, and refuses it (429) over the user's hourly limit or a spent
    budget; unless one of the user's companies topped up, also once today's AI spend cap is
    reached (503). Its transcript is then sent as a message, which counts as one."""
    if not await any_paid(redis, company_ids):
        await refuse_if_capped(redis, user_id=user_id)

    await check_budgets(redis, user_id, None, False)
    key = f"rate:assistant:transcribe:hour:{user_id}"
    await hit(redis, key, "TRANSCRIPTIONS_PER_USER_HOUR", user_id=user_id)


async def record(redis, user_id: str, company_id: UUID | None, tokens: int) -> None:
    """Adds a finished turn's tokens to its budgets. Going over refuses the next message, not
    this one; with Redis down, the turn's spending is lost rather than the answer."""
    try:
        paid = await company_paid(redis, company_id)
    except RedisError:
        paid = False

    for key, name in budgets(user_id, company_id, paid):
        await add_spent(redis, key, tokens, name, company_id=company_id, user_id=user_id)


async def shared_budgets(redis) -> list[BudgetOut]:
    """How much of the budgets for everyone is used today: tokens and messages."""
    found = []

    for name, key, unit in (
        ("TOKENS_PER_DAY", ALL_TOKENS_KEY, "tokens"),
        ("MESSAGES_PER_DAY", ALL_MESSAGES_KEY, "calls"),
    ):
        used = int(await redis.get(key) or 0)
        found.append(BudgetOut(name=name, used=used, limit=await limit(redis, name), unit=unit))

    return found
