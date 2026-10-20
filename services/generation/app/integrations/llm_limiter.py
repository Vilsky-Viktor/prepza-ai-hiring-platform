import asyncio
import logging
import random
import time

from langchain_core.rate_limiters import BaseRateLimiter
from prepza_common.limits import EVERYONE, limit, record_hit

from app.constants.generation import LLM_RATE_KEY, LLM_WAIT_JITTER_SECONDS
from app.integrations.redis import get_redis

logger = logging.getLogger(__name__)


class SharedRateLimiter(BaseRateLimiter):
    """At most GENERATION_CALLS_PER_SECOND LLM requests a second (as set in the Controls tab)
    across every generation process.

    Counted in Redis per second, so the API and all workers share one budget. Chat (rounds)
    isn't limited here, which keeps it ahead of bulk generation.
    """

    def acquire(self, *, blocking: bool = True) -> bool:
        # Every call here is async; a sync call isn't held back.
        return True

    async def aacquire(self, *, blocking: bool = True) -> bool:
        waited = False

        while True:
            second = int(time.time())

            try:
                per_second = await limit(get_redis(), "GENERATION_CALLS_PER_SECOND")

                async with get_redis().pipeline(transaction=True) as pipe:
                    pipe.incr(f"{LLM_RATE_KEY}:{second}")
                    pipe.expire(f"{LLM_RATE_KEY}:{second}", 2)
                    count, _ = await pipe.execute()
            except Exception:
                # Without Redis, generation goes on unlimited rather than stopping.
                logger.exception("Couldn't check the LLM rate limit")

                return True

            if count <= per_second:
                return True

            if not blocking:
                return False

            # Waiting for our own limit on OpenAI's requests, recorded once a request.
            if not waited:
                waited = True
                await record_hit("OPENAI_THROTTLED", kind="provider:openai", scope=EVERYONE)

            until_next = max(0.0, second + 1 - time.time())
            await asyncio.sleep(until_next + random.uniform(0, LLM_WAIT_JITTER_SECONDS))
