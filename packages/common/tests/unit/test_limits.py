import asyncio
import time

import pytest
from fake_redis import DownRedis, FakeRedis
from fastapi import HTTPException
from prepza_common import memory_cache, pubsub
from prepza_common.ai_constants import LIMIT_HIT
from prepza_common.constants import EVENT_ID_ATTRIBUTE
from prepza_common.limit_list import LIMITS, LIMITS_CACHE_SECONDS
from prepza_common.limits import at_most, limit, question_seconds, record_hit


def test_every_default_is_within_its_bounds_and_every_pair_is_a_limit():
    for name, found in LIMITS.items():
        assert found.lowest <= found.default <= found.highest, name
        # Only a plain value may be 0 (a share of none); a limit of 0 would refuse everything.
        assert found.lowest > 0 or not found.counted, name
        assert found.pair is None or found.pair in LIMITS, name
        # A plain value counts nothing, so it counts over no window.
        assert found.counted or found.window is None, name


@pytest.mark.parametrize(
    ("name", "service", "default", "lowest", "highest"),
    [
        ("INTERVIEW_QUESTIONS_PER_TOPIC", "generation", 70, 10, 500),
        ("TEMPLATE_QUESTIONS_PER_TOPIC", "generation", 90, 10, 500),
        ("MAX_TOPICS", "generation", 10, 1, 20),
        ("MAX_SUBTOPICS", "generation", 5, 1, 20),
        ("MONTHLY_BUDGET", "billing", 300.0, 0.0, 100_000.0),
    ],
)
def test_the_question_sizes_topic_caps_and_budget_are_plain_values_in_controls(
    name, service, default, lowest, highest
):
    found = LIMITS[name]

    assert (found.service, found.default, found.lowest, found.highest) == (
        service,
        default,
        lowest,
        highest,
    )
    assert type(found.default) is type(default)
    assert not found.counted and found.window is None
    assert asyncio.run(limit(FakeRedis({name: str(highest)}), name)) == highest


@pytest.mark.parametrize(
    ("edited", "seconds"), [({}, [60, 60, 75]), ({"QUESTION_SECONDS_HARD": "90.0"}, [60, 60, 90])]
)
def test_a_new_tests_seconds_a_question_are_its_levels_as_set_in_controls(edited, seconds):
    redis = FakeRedis(edited)
    levels = ("basic", "medium", "hard")

    assert [asyncio.run(question_seconds(redis, level)) for level in levels] == seconds


def test_a_limit_is_its_default_until_edited():
    assert asyncio.run(limit(FakeRedis(), "MAX_API_KEYS")) == LIMITS["MAX_API_KEYS"].default


def test_an_edited_limit_has_its_new_value_of_the_defaults_type():
    redis = FakeRedis({"MAX_API_KEYS": "12.0", "AI_SPEND_UNPAID_DAY": "20.5"})

    assert asyncio.run(limit(redis, "MAX_API_KEYS")) == 12
    assert isinstance(asyncio.run(limit(redis, "MAX_API_KEYS")), int)
    assert asyncio.run(limit(redis, "AI_SPEND_UNPAID_DAY")) == 20.5


def test_a_value_that_isnt_a_number_falls_back_to_the_default():
    redis = FakeRedis({"MAX_API_KEYS": "lots"})

    assert asyncio.run(limit(redis, "MAX_API_KEYS")) == LIMITS["MAX_API_KEYS"].default


def test_with_redis_down_and_nothing_read_before_every_limit_is_at_its_default():
    assert asyncio.run(limit(DownRedis(), "MAX_WEBHOOKS")) == LIMITS["MAX_WEBHOOKS"].default


def test_with_redis_down_the_last_values_read_stay_in_effect(monkeypatch):
    now = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: now)
    asyncio.run(limit(FakeRedis({"MAX_WEBHOOKS": "40"}), "MAX_WEBHOOKS"))
    monkeypatch.setattr(time, "monotonic", lambda: now + LIMITS_CACHE_SECONDS + 1)

    assert asyncio.run(limit(DownRedis(), "MAX_WEBHOOKS")) == 40


def test_a_change_is_in_effect_once_the_cached_values_expire(monkeypatch):
    now = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: now)
    redis = FakeRedis({"MAX_API_KEYS": 12})
    asyncio.run(limit(redis, "MAX_API_KEYS"))
    redis.limits["MAX_API_KEYS"] = "15"

    # Within the cache's time, the old value; after it, the new one.
    assert asyncio.run(limit(redis, "MAX_API_KEYS")) == 12
    monkeypatch.setattr(time, "monotonic", lambda: now + LIMITS_CACHE_SECONDS + 1)
    assert asyncio.run(limit(redis, "MAX_API_KEYS")) == 15
    assert memory_cache.get("limits:values") == {"MAX_API_KEYS": 15.0}


def test_a_hit_is_recorded_with_its_limits_scope_unless_given(published):
    asyncio.run(record_hit("MAX_API_KEYS", company_id="c1", user_id="u1"))
    asyncio.run(record_hit("OPENAI_QUOTA", kind="provider:openai", what="help_chat"))
    asyncio.run(record_hit("ATS_RATE_LIMIT", kind="provider:ats", scope="company"))

    assert published == [
        (
            LIMIT_HIT,
            {
                "limit": "MAX_API_KEYS",
                "kind": "ours",
                "scope": "company",
                "company_id": "c1",
                "user_id": "u1",
                "what": None,
            },
        ),
        (
            LIMIT_HIT,
            {
                "limit": "OPENAI_QUOTA",
                "kind": "provider:openai",
                "scope": "everyone",
                "company_id": None,
                "user_id": None,
                "what": "help_chat",
            },
        ),
        (
            LIMIT_HIT,
            {
                "limit": "ATS_RATE_LIMIT",
                "kind": "provider:ats",
                "scope": "company",
                "company_id": None,
                "user_id": None,
                "what": None,
            },
        ),
    ]


def test_a_failed_publish_is_tried_again_then_given_up_without_raising(monkeypatch):
    tries = []

    async def down(messages, timeout=None):
        tries.append(messages[0]["attributes"][EVENT_ID_ATTRIBUTE])
        raise ConnectionError("Pub/Sub is down")

    monkeypatch.setattr(pubsub, "publish_batch", down)
    asyncio.run(record_hit("MAX_API_KEYS"))

    # Each try under the same event id, so one that got through is stored once.
    assert len(tries) == 3 and len(set(tries)) == 1


def test_at_most_refuses_one_more_once_the_count_reaches_the_limit(published):
    redis = FakeRedis({"MAX_WEBHOOKS": 2})
    asyncio.run(at_most(redis, "MAX_WEBHOOKS", 1, 409, "Up to {limit} web hooks."))

    with pytest.raises(HTTPException) as refused:
        asyncio.run(at_most(redis, "MAX_WEBHOOKS", 2, 409, "Up to {limit} web hooks."))

    assert (refused.value.status_code, refused.value.detail) == (409, "Up to 2 web hooks.")
    assert [data["limit"] for _, data in published] == ["MAX_WEBHOOKS"]
