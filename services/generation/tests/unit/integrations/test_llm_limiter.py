import asyncio

from fake_redis import FakeRedis
from prepza_common.ai.ai_constants import LIMIT_HIT
from prepza_common.http import pacing

from generation.constants.generation import LLM_RATE_KEY, LLM_WAIT_JITTER_SECONDS
from generation.integrations import llm_limiter
from generation.integrations.llm_limiter import SharedRateLimiter


def test_requests_over_the_limit_wait_for_the_next_second(monkeypatch):
    """At the rate set in the Controls tab."""
    redis = FakeRedis({"GENERATION_CALLS_PER_SECOND": 2})
    monkeypatch.setattr(llm_limiter, "get_redis", lambda: redis)
    monkeypatch.setattr(pacing.time, "time", lambda: 1000.5)
    limiter = SharedRateLimiter()

    async def three():
        return [await limiter.aacquire(blocking=False) for _ in range(3)]

    assert asyncio.run(three()) == [True, True, False]


def test_without_redis_requests_are_not_held_back(monkeypatch):
    monkeypatch.setattr(llm_limiter, "get_redis", lambda: FakeRedis(down=True))

    assert asyncio.run(SharedRateLimiter().aacquire()) is True


def test_waiting_for_the_next_second_is_recorded_once_a_request(monkeypatch, events):
    redis = FakeRedis({"GENERATION_CALLS_PER_SECOND": 1})
    now = [1000.5]

    async def next_second(seconds):
        now[0] += 1

    monkeypatch.setattr(llm_limiter, "get_redis", lambda: redis)
    monkeypatch.setattr(pacing.time, "time", lambda: now[0])
    monkeypatch.setattr(pacing.asyncio, "sleep", next_second)
    # The next second is taken already too, so the second request waits two seconds.
    redis.counts[f"{LLM_RATE_KEY}:1001"] = 1
    limiter = SharedRateLimiter()

    async def two():
        return [await limiter.aacquire(), await limiter.aacquire()]

    assert asyncio.run(two()) == [True, True]
    assert now[0] == 1002.5
    hits = [data for kind, data in events if kind == LIMIT_HIT]
    assert [(hit["limit"], hit["kind"], hit["scope"]) for hit in hits] == [
        ("OPENAI_THROTTLED", "provider:openai", "everyone")
    ]


def test_the_rate_is_24_a_second_until_it_is_set_in_controls(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(llm_limiter, "get_redis", lambda: redis)
    monkeypatch.setattr(pacing.time, "time", lambda: 1000.5)
    limiter = SharedRateLimiter()

    async def many():
        return [await limiter.aacquire(blocking=False) for _ in range(25)]

    assert asyncio.run(many()) == [True] * 24 + [False]


def test_held_calls_ask_again_at_different_moments_of_the_next_second(monkeypatch):
    redis = FakeRedis({"GENERATION_CALLS_PER_SECOND": 1})
    now = [1000.5]
    waits = []

    async def wait(seconds):
        waits.append(seconds)
        now[0] = 1001.5

    monkeypatch.setattr(llm_limiter, "get_redis", lambda: redis)
    monkeypatch.setattr(pacing.time, "time", lambda: now[0])
    monkeypatch.setattr(pacing.asyncio, "sleep", wait)
    monkeypatch.setattr(pacing.random, "uniform", lambda low, high: high)
    redis.counts[f"{LLM_RATE_KEY}:1000"] = 1

    assert asyncio.run(SharedRateLimiter().aacquire()) is True
    # Half a second to the next one, and the jitter on top.
    assert waits == [0.5 + LLM_WAIT_JITTER_SECONDS]
