from functools import cache

from prepza_common.redis.redis_client import redis_client
from redis.asyncio import Redis

from rounds.config import settings


@cache
def get_redis() -> Redis:
    return redis_client(settings.redis_url)
