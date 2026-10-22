from prepza_common.constants import (
    REDIS_HEALTH_CHECK_SECONDS,
    REDIS_RETRIES,
    REDIS_TIMEOUT_SECONDS,
)
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialWithJitterBackoff
from redis.exceptions import ConnectionError, TimeoutError


def redis_client(url: str) -> Redis:
    """Each service's Redis: rate limits, the switches (pause, maintenance) and caches; events go
    through Pub/Sub. A dropped connection is replaced and the command tried again, so a Redis
    restart doesn't fail the requests that were using it. Rate limits may then count a command
    twice, which errs on the safe side."""
    return Redis.from_url(
        url,
        retry=Retry(ExponentialWithJitterBackoff(), REDIS_RETRIES),
        retry_on_error=[ConnectionError, TimeoutError],
        health_check_interval=REDIS_HEALTH_CHECK_SECONDS,
        socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
        socket_timeout=REDIS_TIMEOUT_SECONDS,
    )
