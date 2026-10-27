import asyncio

from fake_redis import DownRedis, FakeRedis
from prepza_common.http import pacing

KEY = "pace:test"


def test_requests_past_the_seconds_share_dont_fit(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(pacing.time, "time", lambda: 1000.5)

    async def three():
        return [await pacing.take_turn(redis, KEY, 2) for _ in range(3)]

    assert asyncio.run(three()) == [True, True, False]
    # Each second's counter expires on its own.
    assert redis.expiries[f"{KEY}:1000"] == pacing.PACE_KEY_SECONDS


def test_a_held_request_waits_for_the_next_second_with_jitter(monkeypatch):
    redis = FakeRedis()
    redis.counts[f"{KEY}:1000"] = 1
    now = [1000.25]
    waits = []

    async def sleep(seconds):
        waits.append(seconds)
        now[0] = 1001.25

    monkeypatch.setattr(pacing.time, "time", lambda: now[0])
    monkeypatch.setattr(pacing.asyncio, "sleep", sleep)
    monkeypatch.setattr(pacing.random, "uniform", lambda low, high: high)

    assert asyncio.run(pacing.wait_turn(redis, KEY, 1, jitter=0.3)) is True
    assert waits == [0.75 + 0.3]


def test_a_request_that_fits_doesnt_wait(monkeypatch):
    async def sleep(seconds):
        raise AssertionError("waited")

    monkeypatch.setattr(pacing.asyncio, "sleep", sleep)

    assert asyncio.run(pacing.wait_turn(FakeRedis(), KEY, 1)) is False


def test_with_redis_down_requests_go_on_unpaced():
    assert asyncio.run(pacing.take_turn(DownRedis(), KEY, 1)) is True
    assert asyncio.run(pacing.wait_turn(DownRedis(), KEY, 1)) is False
