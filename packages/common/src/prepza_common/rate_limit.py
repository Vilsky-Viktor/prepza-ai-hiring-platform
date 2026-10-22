"""Counting uses and costs against our limits (limit_list.LIMITS), by name: each one's value is
the current one (limits.limit) and its window the list's. A refusal is recorded
(limits.record_hit) and answers 429 with its message, in which "{limit}" is the limit's value."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from prepza_common import error_codes
from prepza_common.constants import RATE_LIMITED, RETRY_AFTER
from prepza_common.i18n import TemplateError
from prepza_common.limit_list import LIMITS
from prepza_common.limits import limit, record_hit

logger = logging.getLogger(__name__)


async def counted(redis, key: str, amount: int, window: int) -> tuple[int, int]:
    """Adds `amount` to the window's total under `key`; the total, and the seconds left until
    the window ends."""
    # One transaction, so the counter never exists without its expiry.
    async with redis.pipeline(transaction=True) as pipe:
        pipe.set(key, 0, ex=window, nx=True)
        pipe.incrby(key, amount)
        pipe.ttl(key)
        _, total, seconds = await pipe.execute()

    return total, seconds


def until_tomorrow(now: datetime | None = None) -> dict[str, str]:
    """The Retry-After header of a daily cap (UTC days): the seconds until the next day starts."""
    now = now or datetime.now(UTC)
    tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), UTC)

    return {RETRY_AFTER: str(max(int((tomorrow - now).total_seconds()), 1))}


async def refuse(name: str, value: float, message: str, seconds: int, company_id, user_id) -> None:
    """Records the refusal and answers 429, with Retry-After saying when the window ends."""
    await record_hit(name, company_id=company_id, user_id=user_id)

    retry_after = {RETRY_AFTER: str(max(seconds, 1))}

    raise TemplateError(
        status.HTTP_429_TOO_MANY_REQUESTS,
        message,
        headers=retry_after,
        code=error_codes.RATE_LIMITED,
        limit=value,
    )


async def hit(
    redis,
    key: str,
    name: str,
    message: str = RATE_LIMITED,
    *,
    company_id: object | None = None,
    user_id: str | None = None,
) -> None:
    """Counts one use of limit `name` under `key`; over it, refused. With Redis down, an
    error: the request fails rather than going unlimited (see hit_or_skip). `company_id` and
    `user_id` say whose refusal it was, for the record."""
    await spend(redis, key, 1, name, message, company_id=company_id, user_id=user_id)


async def spend(
    redis,
    key: str,
    amount: int,
    name: str,
    message: str = RATE_LIMITED,
    *,
    company_id: object | None = None,
    user_id: str | None = None,
) -> None:
    """Adds `amount` (a cost, such as tokens) to limit `name`'s total under `key`; once the
    total is over the limit, refused. An `amount` of 0 only checks it. With Redis down, an
    error, as with hit."""
    value = await limit(redis, name)

    if value <= 0:
        return

    total, seconds = await counted(redis, key, amount, LIMITS[name].window)

    if total > value:
        await refuse(name, value, message, seconds, company_id, user_id)


async def hit_or_skip(
    redis,
    key: str,
    name: str,
    message: str = RATE_LIMITED,
    *,
    company_id: object | None = None,
    user_id: str | None = None,
) -> None:
    """hit(), except that with Redis down the use goes uncounted rather than refused: for limits
    against abuse, where refusing everyone while Redis is down would be worse."""
    try:
        await hit(redis, key, name, message, company_id=company_id, user_id=user_id)
    except HTTPException:
        raise
    except Exception:
        logger.warning("The %s limit skipped, Redis failed", name, exc_info=True)


async def add_spent(
    redis, key: str, amount: int, name: str, *, company_id=None, user_id=None
) -> None:
    """Adds what a finished request cost to its budget. Going over refuses the next request,
    not this one; with Redis down, the cost is lost rather than the request's result."""
    try:
        value = await limit(redis, name)

        if value > 0:
            await counted(redis, key, amount, LIMITS[name].window)
    except Exception:
        logger.warning("Spending on %s not counted, Redis failed", name, exc_info=True)


def recipient_key(email: str) -> str:
    """An address as the per-recipient email limit counts it: lowercased and without a +tag, as
    name+1@ and name+2@ reach one inbox. Only for the limit's key; the email still goes to the
    address as given."""
    local, at, domain = email.strip().lower().rpartition("@")

    if not at:
        return domain

    return f"{local.split('+', 1)[0]}@{domain}"


async def hit_emails(redis, sender: str, recipient: str, company_id: object | None = None) -> None:
    """Limits invite emails, so nobody can spam from our domain.

    The sender's counts are shared by every service that sends invites. `recipient` names the
    address (its recipient_key) and what it's invited to, so resending to one person is limited
    on its own.
    """
    who = {"company_id": company_id, "user_id": sender}
    # The narrower key first: one address refused doesn't use up the sender's counts.
    await hit(redis, f"rate:emails:recipient:{recipient}", "EMAIL_RECIPIENT_DAILY_LIMIT", **who)
    await hit(redis, f"rate:emails:hour:{sender}", "EMAIL_HOURLY_LIMIT", **who)
    await hit(redis, f"rate:emails:day:{sender}", "EMAIL_DAILY_LIMIT", **who)
