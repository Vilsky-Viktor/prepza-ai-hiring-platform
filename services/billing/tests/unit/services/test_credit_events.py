"""credits.added, which tells other services an owner got credits: saved through the outbox with
the credits it announces (a top-up, a referral reward, a chargeback reversed), never for
credits taken back or for Paddle's repeat."""

import asyncio

import pytest

from billing.repositories import purchases
from billing.repositories import referrals as referrals_storage
from billing.services import topups, webhooks
from tests.unit.paddle_events import adjustment, completed

CREDITS_ADDED = "credits.added"


def added(owner_id):
    return (CREDITS_ADDED, {"owner_type": "company", "owner_id": owner_id})


@pytest.fixture
def saved(monkeypatch):
    """The credits.added events saved with the changes, as (type, data)."""
    found = []

    async def nothing(*args, **kwargs):
        pass

    monkeypatch.setattr(topups.outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(topups, "track", nothing)

    return found


@pytest.fixture
def top_up(monkeypatch, saved):
    """A top-up whose grant is new (or Paddle's repeat) and whose referral pays `referrer`."""
    state = {"granted": True, "referrer": None}

    async def grant(session, *args):
        if state["granted"]:
            saved.extend(event for event in args[11](0) if event[0] == CREDITS_ADDED)

        return state["granted"]

    async def reward(session, owner_type, owner_id, transaction_id, events_for=lambda _: []):
        if state["referrer"] is None:
            return None

        saved.extend(e for e in events_for(state["referrer"]) if e[0] == CREDITS_ADDED)

        return state["referrer"]

    monkeypatch.setattr(purchases, "grant", grant)
    monkeypatch.setattr(referrals_storage, "reward", reward)

    return state


def test_a_new_top_up_saves_that_the_company_got_credits(top_up, saved):
    asyncio.run(webhooks.handle(completed()))

    assert saved == [added("acme")]


def test_paddles_repeat_of_a_top_up_saves_nothing_again(top_up, saved):
    top_up["granted"] = False
    asyncio.run(webhooks.handle(completed()))

    assert saved == []


def test_a_referral_reward_tells_both_companies_once_each(top_up, saved):
    top_up["referrer"] = "bob"
    asyncio.run(webhooks.handle(completed()))

    # The referrer for its reward; the company that topped up for its top-up, once.
    assert sorted(event[1]["owner_id"] for event in saved) == ["acme", "bob"]


@pytest.fixture
def adjusted(monkeypatch, saved):
    async def bought(session, transaction_id):
        return ("company", "acme", 1_000, 1000)

    async def take_back_credits(session, *args):
        saved.extend(args[8])

        return 0

    async def take_back(session, transaction_id):
        return False

    monkeypatch.setattr(purchases, "for_transaction", bought)
    monkeypatch.setattr(purchases, "take_back", take_back_credits)
    monkeypatch.setattr(referrals_storage, "take_back", take_back)


def test_a_reversed_chargeback_saves_that_the_company_got_credits(adjusted, saved):
    asyncio.run(webhooks.handle(adjustment(action="chargeback_reverse")))

    assert saved == [added("acme")]


@pytest.mark.parametrize("action", ["refund", "chargeback"])
def test_credits_taken_back_tell_nobody(adjusted, saved, action):
    asyncio.run(webhooks.handle(adjustment(action=action)))

    assert saved == []


def test_a_slow_pub_sub_delays_paddles_answer_once_not_once_a_message(top_up, monkeypatch):
    import time

    async def slow(*args, **kwargs):
        await asyncio.sleep(0.3)

    monkeypatch.setattr(topups, "track", slow)
    monkeypatch.setattr(topups.outbox_service, "flush_quietly", slow)
    started = time.monotonic()
    asyncio.run(webhooks.handle(completed()))

    # Two waits of 0.3 s each: together, not one after another (0.6 s).
    assert time.monotonic() - started < 0.5
