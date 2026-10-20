import asyncio

import pytest
from prepza_common.constants import PUBLISH_IN_REQUEST_TIMEOUT_SECONDS

from app.services import credit_events, referrals, webhooks
from app.storage import purchases
from app.storage import referrals as referrals_storage
from tests.unit.paddle_events import adjustment, completed


@pytest.fixture
def published(monkeypatch):
    """The credits.added events billing publishes, as (type, data, timeout)."""
    sent = []

    async def fake_publish(event_type, data, timeout):
        sent.append((event_type, data, timeout))

    async def quietly(event):
        pass

    monkeypatch.setattr(credit_events.pubsub, "publish", fake_publish)
    monkeypatch.setattr(referrals, "publish_quietly", quietly)

    return sent


def added(owner_id):
    return (
        "credits.added",
        {"owner_type": "company", "owner_id": owner_id},
        PUBLISH_IN_REQUEST_TIMEOUT_SECONDS,
    )


@pytest.fixture
def top_up(monkeypatch):
    """A top-up whose grant is new (or Paddle's repeat) and whose referral pays `referrer`."""
    state = {"granted": True, "referrer": None, "grants": 0}

    async def grant(*args):
        state["grants"] += 1

        return state["granted"]

    async def reward(owner_type, owner_id, transaction_id):
        return state["referrer"]

    monkeypatch.setattr(purchases, "grant", grant)
    monkeypatch.setattr(referrals_storage, "reward", reward)

    return state


def test_a_new_top_up_tells_that_the_company_got_credits(top_up, published):
    asyncio.run(webhooks.handle(completed()))

    assert published == [added("acme")]


def test_paddles_repeat_of_a_top_up_tells_nobody_again(top_up, published):
    top_up["granted"] = False
    asyncio.run(webhooks.handle(completed()))

    assert published == []


def test_a_referral_reward_tells_both_companies_once_each(top_up, published):
    top_up["referrer"] = "bob"
    asyncio.run(webhooks.handle(completed()))

    # The referrer for its reward; the company that topped up for its top-up, once.
    assert sorted(event[1]["owner_id"] for event in published) == ["acme", "bob"]


def test_a_failing_publish_still_adds_the_credits(top_up, monkeypatch):
    async def down(*args):
        raise RuntimeError("Pub/Sub down")

    monkeypatch.setattr(credit_events.pubsub, "publish", down)
    asyncio.run(webhooks.handle(completed()))

    assert top_up["grants"] == 1


@pytest.fixture
def adjusted(monkeypatch):
    async def bought(transaction_id):
        return ("company", "acme", 1_000, "1000")

    async def take_back_credits(*args):
        return 0

    async def take_back(transaction_id):
        return False

    monkeypatch.setattr(purchases, "for_transaction", bought)
    monkeypatch.setattr(purchases, "take_back", take_back_credits)
    monkeypatch.setattr(referrals_storage, "take_back", take_back)


def test_a_reversed_chargeback_tells_that_the_company_got_credits(adjusted, published):
    asyncio.run(webhooks.handle(adjustment(action="chargeback_reverse")))

    assert published == [added("acme")]


@pytest.mark.parametrize("action", ["refund", "chargeback"])
def test_credits_taken_back_tell_nobody(adjusted, published, action):
    asyncio.run(webhooks.handle(adjustment(action=action)))

    assert published == []


def test_a_slow_pub_sub_delays_paddles_answer_once_not_once_a_message(top_up, monkeypatch):
    import time

    from app.services import topups

    async def slow(*args, **kwargs):
        await asyncio.sleep(0.3)

    monkeypatch.setattr(credit_events.pubsub, "publish", slow)
    monkeypatch.setattr(topups, "track", slow)
    monkeypatch.setattr(topups.outbox_service, "flush_quietly", slow)
    started = time.monotonic()
    asyncio.run(webhooks.handle(completed()))

    # Three messages of 0.3 s each: sent together, not one after another (0.9 s).
    assert time.monotonic() - started < 0.6
