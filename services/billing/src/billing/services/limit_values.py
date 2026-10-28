"""The limits superadmins edit in Controls: kept in Postgres, and written to Redis's
limits:values hash, which every service reads (on each change and every LIMITS_SYNC_SECONDS,
so a Redis wipe heals itself and never brings back old values; not at start, which a cold start
would wait on, Redis down included)."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.i18n.i18n import TemplateError
from prepza_common.limits.limit_list import LIMITS, LIMITS_KEY, PROVIDER_LIMITS

from billing.constants.usage import HITS_DAYS, OUT_OF_BOUNDS, UNKNOWN_LIMIT
from billing.integrations.redis import get_redis
from billing.repositories import limit_hits, limit_settings
from billing.schemas.limits import LimitOut, LimitsOut, ProviderLimitOut


async def sync() -> None:
    values = await limit_settings.values()

    async with get_redis().pipeline(transaction=True) as pipe:
        pipe.delete(LIMITS_KEY)

        if values:
            pipe.hset(LIMITS_KEY, mapping={name: str(value) for name, value in values.items()})

        await pipe.execute()


def known(name: str):
    found = LIMITS.get(name)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, UNKNOWN_LIMIT)

    return found


def number(value: float, default: float) -> float:
    """Whole numbers for limits that count; USD keeps its cents."""
    return round(value) if isinstance(default, int) else round(value, 2)


async def change(name: str, value: float | None, user: User) -> None:
    """Sets the limit (None: back to its default) within its bounds, then tells the services."""
    found = known(name)

    if value is not None:
        value = number(value, found.default)

        if not found.lowest <= value <= found.highest:
            bounds = {"lowest": found.lowest, "highest": found.highest}

            raise TemplateError(status.HTTP_422_UNPROCESSABLE_CONTENT, OUT_OF_BOUNDS, **bounds)

        if value == found.default:
            value = None

    await limit_settings.change(name, value, user.uid, user.email)
    await sync()


async def limits_out() -> LimitsOut:
    """Every limit, its unpaid counterpart beside its paid one, with its hits of the last
    HITS_DAYS days; then the providers' limits, read-only."""
    values = await limit_settings.values()
    hits = await limit_hits.counts_since(datetime.now(UTC) - timedelta(days=HITS_DAYS))
    shown = {}

    for name, found in LIMITS.items():
        value = values.get(name, found.default)
        shown[name] = LimitOut(
            name=name,
            service=found.service,
            value=value,
            default=found.default,
            changed=name in values,
            unit=found.unit,
            window=found.window,
            lowest=found.lowest,
            highest=found.highest,
            scope=found.scope,
            audience=found.audience,
            counted=found.counted,
            hits=hits.get(name, 0),
        )

    for name, found in LIMITS.items():
        if found.pair:
            shown[found.pair].unpaid = shown.pop(name)

    providers = [
        ProviderLimitOut(name=name, provider=provider, hits=hits.get(name, 0))
        for name, provider in PROVIDER_LIMITS.items()
    ]

    return LimitsOut(limits=list(shown.values()), providers=providers, hits_days=HITS_DAYS)
