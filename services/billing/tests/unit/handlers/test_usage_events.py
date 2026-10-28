"""Billing's consumption of the services' records of AI calls and limit hits."""

import asyncio
from datetime import UTC, datetime

import pytest
from event_pushes import push
from prepza_common.ai.ai_constants import AI_USED, LIMIT_HIT, Category

from billing.handlers import ai_used, dispatch
from billing.helpers.usage import category_of
from billing.services import usage

WHEN = datetime(2026, 10, 16, 9, tzinfo=UTC)
CALL = {"action": "assistant_message", "company_id": "c1", "cost_usd": 0.25}


@pytest.fixture
def stored(monkeypatch):
    """The rows stored and the unpaid spend added; an event id stored before stores nothing."""
    state = {"usage": {}, "hits": {}, "unpaid": [], "category": Category.UNPAID}

    async def record_usage(event_id, occurred_at, data):
        if event_id in state["usage"]:
            return None

        state["usage"][event_id] = (occurred_at, data)

        return state["category"]

    async def record_hit(event_id, occurred_at, data):
        state["hits"].setdefault(event_id, (occurred_at, data))

    async def add_unpaid(redis, cost_usd):
        state["unpaid"].append(cost_usd)

    monkeypatch.setattr(usage, "record_usage", record_usage)
    monkeypatch.setattr(usage, "record_hit", record_hit)
    monkeypatch.setattr(ai_used, "add_unpaid", add_unpaid)
    monkeypatch.setattr(ai_used, "get_redis", lambda: None)

    return state


@pytest.mark.parametrize("category", [Category.UNPAID, Category.NO_COMPANY])
def test_an_unpaid_call_is_stored_and_counted_toward_the_cap(stored, category):
    stored["category"] = category
    asyncio.run(dispatch.handle(AI_USED, CALL, "e1", WHEN))

    assert stored["usage"] == {"e1": (WHEN, CALL)}
    assert stored["unpaid"] == [0.25]


@pytest.mark.parametrize("category", [Category.PAID, Category.PREPZA])
def test_a_paid_companys_or_prepzas_call_never_counts_toward_the_cap(stored, category):
    stored["category"] = category
    asyncio.run(dispatch.handle(AI_USED, CALL, "e1", WHEN))

    assert list(stored["usage"]) == ["e1"]
    assert stored["unpaid"] == []


def test_a_redelivered_call_is_stored_and_counted_once(stored):
    for _ in range(3):
        asyncio.run(dispatch.handle(AI_USED, CALL, "e1", WHEN))

    assert list(stored["usage"]) == ["e1"]
    assert stored["unpaid"] == [0.25]


def test_a_call_that_cost_nothing_adds_nothing(stored):
    asyncio.run(dispatch.handle(AI_USED, {**CALL, "cost_usd": 0.0}, "e1", WHEN))

    assert stored["unpaid"] == []


def test_with_redis_down_the_call_is_still_stored(stored, monkeypatch):
    async def down(redis, cost_usd):
        raise ConnectionError("Redis is down")

    monkeypatch.setattr(ai_used, "add_unpaid", down)
    asyncio.run(dispatch.handle(AI_USED, CALL, "e1", WHEN))

    assert list(stored["usage"]) == ["e1"]


def test_a_limit_hit_is_stored_and_other_events_are_ignored(stored):
    hit = {"limit": "MAX_API_KEYS", "kind": "ours", "scope": "company"}
    asyncio.run(dispatch.handle(LIMIT_HIT, hit, "h1", WHEN))
    asyncio.run(dispatch.handle("candidate.finished", {"x": 1}, "o1", WHEN))

    assert stored["hits"] == {"h1": (WHEN, hit)}
    assert stored["usage"] == {}


def test_pubsub_pushes_events_to_billing(client, stored):
    body = push(AI_USED, CALL, "e9", occurred_at=WHEN)

    assert client.post("/internal/events", json=body).status_code == 204
    assert stored["usage"] == {"e9": (WHEN, CALL)}


@pytest.mark.parametrize(
    ("action", "company_id", "paid", "category"),
    [
        ("interview_generation", "c1", True, Category.PAID),
        ("interview_generation", "c1", False, Category.UNPAID),
        # A company's call is the company's, even of an action prepza also does for itself.
        ("embeddings", "c1", False, Category.UNPAID),
        ("template_generation", None, False, Category.PREPZA),
        ("help_chat", None, False, Category.NO_COMPANY),
    ],
)
def test_who_a_call_was_for(action, company_id, paid, category):
    assert category_of(action, company_id, paid) == category
