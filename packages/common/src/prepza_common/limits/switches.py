"""Switches every service reads (the emergency pause, maintenance mode): each one Redis key
without expiry, read through the per-instance cache, so a request costs no Redis command most of
the time. With Redis down, a switch keeps the last state this instance read, as the limits keep
their last values; one never read is off, so a switch never stops a service by itself."""

import logging

from prepza_common.redis import memory_cache

logger = logging.getLogger(__name__)

# How long an instance keeps the last state it read, for when Redis is down.
LAST_READ_SECONDS = 10 * 365 * 24 * 60 * 60


async def is_on(redis, key: str, seconds: int) -> bool:
    """Whether the switch at `key` is on, read from Redis at most every `seconds` per instance."""
    cached = memory_cache.get(key)

    if cached is not None:
        return cached

    try:
        on = bool(await redis.exists(key))
        memory_cache.put(f"{key}:last", on, LAST_READ_SECONDS)
    except Exception:
        logger.warning("Couldn't read a switch; keeping its last state", exc_info=True)
        on = bool(memory_cache.get(f"{key}:last"))

    memory_cache.put(key, on, seconds)

    return on


def remember(key: str, on: bool, seconds: int) -> None:
    """The instance that turned the switch knows its new state at once; the others within
    `seconds`."""
    memory_cache.put(key, on, seconds)
    memory_cache.put(f"{key}:last", on, LAST_READ_SECONDS)
