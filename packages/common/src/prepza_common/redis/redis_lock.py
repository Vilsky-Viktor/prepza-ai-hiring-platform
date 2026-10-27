"""A lock in Redis for a scheduled run, so two runs at once (a slow one and the next) don't both
work: taken with SET NX and a time it lasts, released only by the run that holds it."""

import uuid

# Deletes the lock only while it still holds this run's token: a run that outlived its lock
# never removes the next run's.
RELEASE = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) end return 0"
)


async def acquire(redis, key: str, seconds: int) -> str | None:
    """Takes the lock for `seconds`; its token, or None when another run holds it."""
    token = uuid.uuid4().hex

    return token if await redis.set(key, token, nx=True, ex=seconds) else None


async def release(redis, key: str, token: str) -> None:
    await redis.eval(RELEASE, 1, key, token)
