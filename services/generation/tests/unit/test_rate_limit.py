import asyncio

import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException
from testee_common.limits.limit_list import LIMITS
from testee_common.limits.rate_limit import hit

KEY = "rate:generations:u1"


def test_hit_allows_up_to_the_limits_edited_value_within_its_window():
    redis = FakeRedis({"GENERATION_LIMIT": 2})
    asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))
    asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))

    assert redis.counts[KEY] == 2
    assert redis.expiries[KEY] == LIMITS["GENERATION_LIMIT"].window


def test_hit_rejects_over_the_limit():
    redis = FakeRedis({"GENERATION_LIMIT": 1})
    asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))

    with pytest.raises(HTTPException) as error:
        asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))

    assert error.value.status_code == 429


def test_without_an_edited_value_the_default_holds():
    redis = FakeRedis()
    redis.counts[KEY] = LIMITS["GENERATION_LIMIT"].default

    with pytest.raises(HTTPException):
        asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))


def test_hit_keeps_the_first_expiry():
    redis = FakeRedis({"GENERATION_LIMIT": 5})
    asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))
    redis.expiries[KEY] = 30
    asyncio.run(hit(redis, KEY, "GENERATION_LIMIT"))

    assert redis.counts[KEY] == 2
    assert redis.expiries[KEY] == 30
