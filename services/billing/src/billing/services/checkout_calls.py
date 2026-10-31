from testee_common.limits.rate_limit import hit_or_skip

from billing.integrations.redis import get_redis


async def count(user_id: str, company_id) -> None:
    """One call to Paddle's API on the user's behalf (a checkout, a card update, an invoice or a
    failure read); past the hourly limit, a 429. Against abuse, so Redis being down lets it
    through."""
    await hit_or_skip(
        get_redis(),
        f"rate:checkout-calls:{user_id}",
        "CHECKOUT_CALLS_PER_USER_HOUR",
        company_id=company_id,
        user_id=user_id,
    )
