from functools import cache

from redis.asyncio import Redis
from testee_common.redis.redis_client import redis_client

from generation.config import settings


@cache
def get_redis() -> Redis:
    """For rate limits, the shared LLM limiter and the draft cache; events go through Pub/Sub."""
    return redis_client(settings.redis_url)
