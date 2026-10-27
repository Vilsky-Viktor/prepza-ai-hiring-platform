import asyncio

import pytest
from fake_redis import FakeRedis
from redis.exceptions import RedisError

from api.services import idempotency


class FlakyRedis(FakeRedis):
    """Takes the claim, then fails: keeping the result (`fail_keep`) or freeing a failed run's
    claim (`fail_free`)."""

    def __init__(self, fail_keep=False, fail_free=False):
        super().__init__()
        self.fail_keep = fail_keep
        self.fail_free = fail_free

    async def set(self, name, value, nx=False, ex=None):
        if self.fail_keep and not nx:
            raise RedisError("Redis went away")

        return await super().set(name, value, nx=nx, ex=ex)

    async def delete(self, name):
        if self.fail_free:
            raise RedisError("Redis went away")

        await super().delete(name)


def test_a_made_result_is_answered_when_redis_fails_to_keep_it(monkeypatch):
    redis = FlakyRedis(fail_keep=True)
    monkeypatch.setattr(idempotency, "get_redis", lambda: redis)
    runs = []

    async def make():
        runs.append(1)

        return "id-1"

    result = asyncio.run(idempotency.once("slot", 60, "req", make))

    assert result == "id-1" and runs == [1]
    # Still claimed: a retry is told the first one runs, never making it twice.
    assert asyncio.run(redis.get("slot")) == b"req:pending"


def test_a_failed_run_raises_its_own_error_when_redis_fails_to_free_its_claim(monkeypatch):
    monkeypatch.setattr(idempotency, "get_redis", lambda: FlakyRedis(fail_free=True))

    async def refused():
        raise ValueError("No credits")

    with pytest.raises(ValueError, match="No credits"):
        asyncio.run(idempotency.once("slot", 60, "req", refused))
