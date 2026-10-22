from langchain_core.rate_limiters import BaseRateLimiter
from prepza_common.limits import EVERYONE, limit, record_hit
from prepza_common.pacing import take_turn, wait_turn

from app.constants.generation import LLM_RATE_KEY, LLM_WAIT_JITTER_SECONDS
from app.integrations.redis import get_redis


class SharedRateLimiter(BaseRateLimiter):
    """At most GENERATION_CALLS_PER_SECOND LLM requests a second (as set in the Controls tab)
    across every generation process.

    Counted in Redis per second (prepza_common.pacing), so the API and all workers share one
    budget; without Redis, generation goes on unlimited rather than stopping. Chat (rounds)
    isn't limited here, which keeps it ahead of bulk generation.
    """

    def acquire(self, *, blocking: bool = True) -> bool:
        # Every call here is async; a sync call isn't held back.
        return True

    async def aacquire(self, *, blocking: bool = True) -> bool:
        redis = get_redis()
        per_second = await limit(redis, "GENERATION_CALLS_PER_SECOND")

        if not blocking:
            return await take_turn(redis, LLM_RATE_KEY, per_second)

        # Waiting for our own limit on OpenAI's requests, recorded once a request.
        if await wait_turn(redis, LLM_RATE_KEY, per_second, LLM_WAIT_JITTER_SECONDS):
            await record_hit("OPENAI_THROTTLED", kind="provider:openai", scope=EVERYONE)

        return True
