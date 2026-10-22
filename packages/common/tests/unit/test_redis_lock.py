import asyncio

from fake_redis import FakeRedis
from prepza_common import redis_lock


def test_a_second_run_waits_for_the_first_to_release_the_lock():
    redis = FakeRedis()

    async def scenario():
        first = await redis_lock.acquire(redis, "job:lock", 60)
        second = await redis_lock.acquire(redis, "job:lock", 60)
        # Another run's token releases nothing.
        await redis_lock.release(redis, "job:lock", "not-mine")
        still = await redis_lock.acquire(redis, "job:lock", 60)
        await redis_lock.release(redis, "job:lock", first)
        after = await redis_lock.acquire(redis, "job:lock", 60)

        return first, second, still, after

    first, second, still, after = asyncio.run(scenario())

    assert first and after
    assert second is None and still is None
