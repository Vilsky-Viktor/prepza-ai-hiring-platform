from functools import cache

from prepza_common.redis.redis_client import redis_client
from redis.asyncio import Redis

from companies.config import settings


@cache
def get_redis() -> Redis:
    """For rate limits; events go through Pub/Sub (prepza_common.events.pubsub)."""
    return redis_client(settings.redis_url)
