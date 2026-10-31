"""Requests paced to a share a second, counted in Redis, so every instance and run takes turns
from one budget (Resend's sends, generation's OpenAI calls). With Redis down a request goes on
unpaced: pacing keeps us under a provider's limit, and the provider's own 429 is still retried."""

import asyncio
import logging
import random
import time

from testee_common.limits.rate_limit import counted

logger = logging.getLogger(__name__)

# A second's counter outlives its second a little, then expires on its own.
PACE_KEY_SECONDS = 2


async def take_turn(redis, key: str, per_second: float) -> bool:
    """Counts one request in this second's share under `key`; whether it fits. With Redis down,
    it fits."""
    try:
        total, _ = await counted(redis, f"{key}:{int(time.time())}", 1, PACE_KEY_SECONDS)
    except Exception:
        logger.warning("Pacing skipped, Redis failed", exc_info=True)

        return True

    return total <= per_second


async def wait_turn(redis, key: str, per_second: float, jitter: float = 0.0) -> bool:
    """Waits until a request fits a second's `per_second` under `key`; whether it had to wait. A
    held request asks again in the next second, up to `jitter` seconds later at random, so the
    held ones don't all ask at the same instant (and collide again, each ask a paid command)."""
    waited = False

    while not await take_turn(redis, key, per_second):
        waited = True
        now = time.time()
        await asyncio.sleep(int(now) + 1 - now + random.uniform(0, jitter))

    return waited
