from functools import cache

from redis.asyncio import Redis
from testee_common.redis.redis_client import redis_client

from billing.config import settings


@cache
def get_redis() -> Redis:
    return redis_client(settings.redis_url)
