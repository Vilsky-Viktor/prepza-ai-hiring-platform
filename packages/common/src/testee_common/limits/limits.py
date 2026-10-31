"""Our limits' current values (limit_list.LIMITS, as edited in the admin zone's Controls tab), and
the record of every refusal, ours or a provider's, which billing stores for the AI costs tab."""

import logging

from testee_common.ai.ai_constants import LIMIT_HIT, RECORD_ATTEMPTS
from testee_common.config.event_constants import PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
from testee_common.events.pubsub import publish_retried
from testee_common.i18n.i18n import TemplateError
from testee_common.limits.limit_list import (
    LIMITS,
    LIMITS_CACHE_SECONDS,
    LIMITS_KEY,
    QUESTION_SECONDS,
)
from testee_common.redis import memory_cache

logger = logging.getLogger(__name__)

OURS = "ours"
EVERYONE = "everyone"
# The last values read from Redis, kept for as long as the instance runs, for when Redis is down.
LAST_READ_KEY = f"{LIMITS_KEY}:last"
LAST_READ_SECONDS = 10 * 365 * 24 * 60 * 60


def parsed(raw: dict) -> dict[str, float]:
    """The hash as Redis gives it (bytes or text), as numbers by name."""
    values = {}

    for name, value in raw.items():
        key = name.decode() if isinstance(name, bytes) else name

        try:
            values[key] = float(value)
        except ValueError:
            logger.warning("Limit %s has a value that isn't a number", key)

    return values


async def current_values(redis) -> dict[str, float]:
    """The edited values, read from Redis at most every LIMITS_CACHE_SECONDS per instance. With
    Redis down, the last values this instance read, so a running service keeps the Controls
    values through an outage; an instance that never read them has none: every limit at its
    default."""
    values = memory_cache.get(LIMITS_KEY)

    if values is not None:
        return values

    try:
        values = parsed(await redis.hgetall(LIMITS_KEY))
        memory_cache.put(LAST_READ_KEY, values, LAST_READ_SECONDS)
    except Exception:
        logger.warning("Couldn't read the limits; using the last ones read", exc_info=True)
        values = memory_cache.get(LAST_READ_KEY) or {}

    memory_cache.put(LIMITS_KEY, values, LIMITS_CACHE_SECONDS)

    return values


async def limit(redis, name: str) -> int | float:
    """The limit's value: as edited in the Controls tab, or its default."""
    default = LIMITS[name].default
    value = (await current_values(redis)).get(name)

    return default if value is None else type(default)(value)


async def question_seconds(redis, level: str) -> int:
    """The seconds each question of a new test of `level` (basic, medium or hard) starts with."""
    return await limit(redis, QUESTION_SECONDS[level])


async def record_hit(
    name: str,
    *,
    kind: str = OURS,
    scope: str | None = None,
    company_id: object | None = None,
    user_id: str | None = None,
    what: str | None = None,
) -> None:
    """Records one refusal: a log line (the testee_limit_hits metric) and an event billing stores.
    `kind` is "ours" or "provider:<name>"; `scope` is the limit's own unless given. Never raises.
    An IP is never recorded, only that its limit was hit."""
    found = LIMITS.get(name)
    scope = scope or (found.scope if found else EVERYONE)
    logger.warning("Limit hit: limit=%s kind=%s scope=%s what=%s", name, kind, scope, what or "")

    if found is not None and scope == EVERYONE:
        # A shared limit: everyone's use of it (the AI's, for most) just stopped.
        logger.error("Shared limit used up: limit=%s", name)

    data = {
        "limit": name,
        "kind": kind,
        "scope": scope,
        "company_id": str(company_id) if company_id else None,
        "user_id": user_id,
        "what": what,
    }
    await publish_retried(LIMIT_HIT, data, RECORD_ATTEMPTS, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS)


async def at_most(
    redis,
    name: str,
    count: int,
    status_code: int,
    message: str,
    *,
    company_id: object | None = None,
    user_id: str | None = None,
    code: str | None = None,
) -> None:
    """Refuses one more of what `count` counts (keys, members, ...) once the limit is reached:
    a `status_code` with `message`, in which "{limit}" is the limit's value, and `code`
    (CodedError)."""
    value = await limit(redis, name)

    if count < value:
        return

    await record_hit(name, company_id=company_id, user_id=user_id)

    raise TemplateError(status_code, message, code=code, limit=value)
