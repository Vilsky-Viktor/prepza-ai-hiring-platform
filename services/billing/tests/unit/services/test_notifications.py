import asyncio
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.events.notifications import NOTIFICATION_REQUESTED, notification

from billing.integrations import paddle
from billing.repositories import auto_top_up_charges, events, purchases
from billing.repositories import auto_top_ups as auto_top_ups_storage
from billing.repositories import referrals as referrals_storage
from billing.services import (
    auto_top_up_charging,
    auto_top_up_declines,
    referrals,
    topups,
    webhooks,
)
from tests.unit.paddle_events import completed


@pytest.fixture
def notified(monkeypatch):
    """The bell's notifications billing saves through its outbox."""
    sent = []

    def tell(session, event):
        sent.append(event)

    async def nothing():
        pass

    monkeypatch.setattr(events, "tell", tell)
    monkeypatch.setattr(auto_top_up_declines.outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(topups.outbox_service, "flush_quietly", nothing)

    return sent


def bells(events) -> list[dict]:
    return [data for kind, data in events if kind == NOTIFICATION_REQUESTED]


def test_a_rewarded_referrer_is_told_with_the_reward(monkeypatch, notified):
    async def rewarded(session, owner_type, owner_id, transaction_id, events_for):
        notified.extend(bells(events_for("bob")))

        return "bob"

    monkeypatch.setattr(referrals_storage, "reward", rewarded)

    asyncio.run(referrals.reward_after_top_up("company", "ann", "txn_01"))

    assert notified == [
        notification(
            "company", "bob", "referral_rewarded", "/companies/bob/referrals", credits=1_000
        )
    ]


@pytest.fixture
def granted(monkeypatch, notified):
    async def fake_grant(session, *args):
        notified.extend(bells(args[11]))

        return True

    async def no_referral(session, owner_type, owner_id, transaction_id, events_for=None):
        return None

    async def owner(session, subscription_id):
        return ("company", "acme")

    monkeypatch.setattr(purchases, "grant", fake_grant)
    monkeypatch.setattr(referrals_storage, "reward", no_referral)
    monkeypatch.setattr(auto_top_ups_storage, "owner_of", owner)


def test_an_automatic_top_up_tells_the_owner_the_credits_it_added(granted, notified):
    event = completed()
    event["data"]["subscription_id"] = "sub_01"

    asyncio.run(webhooks.handle(event))

    assert notified == [
        notification("company", "acme", "auto_top_up_charged", "/top-up", credits=5_000)
    ]


def test_a_top_up_bought_by_hand_tells_nobody(granted, notified):
    asyncio.run(webhooks.handle(completed()))

    assert notified == []


def paddle_error(code):
    request = httpx.Request("POST", "https://paddle.test")

    return httpx.HTTPStatusError(
        "", request=request, response=httpx.Response(code, request=request)
    )


def charge_failing_with(monkeypatch, error):
    """Paddle's charge fails with `error`; the owners marked failed."""

    async def claimed(session, owner_type, owner_id, now):
        return SimpleNamespace(
            subscription_id="sub_01",
            product="topup_50",
            currency="USD",
            price=None,
            price_currency=None,
            language=None,
        )

    async def charge(subscription_id, price_id):
        raise error

    async def no_reason(subscription_id, since, timeout):
        return None

    marked = []

    async def declined(session, owner_type, owner_id, now):
        marked.append(owner_id)

        return False

    async def usd(country, company_id=None):
        return "USD"

    monkeypatch.setattr(auto_top_ups_storage, "claim_charge", claimed)
    monkeypatch.setattr(auto_top_up_charges, "declined", declined)
    monkeypatch.setattr(paddle, "charge", charge)
    monkeypatch.setattr(paddle, "charge_error", no_reason)
    monkeypatch.setattr(auto_top_up_charging, "decide", usd)

    return marked


def test_a_declined_automatic_charge_tells_the_owner(monkeypatch, notified):
    marked = charge_failing_with(monkeypatch, paddle_error(400))

    asyncio.run(auto_top_up_charging.check("company", "acme"))

    assert notified == [notification("company", "acme", "auto_top_up_failed", "/top-up")]
    assert marked == ["acme"]


@pytest.mark.parametrize("error", [httpx.ReadTimeout("timed out"), paddle_error(503)])
def test_an_automatic_charge_paddle_may_have_taken_isnt_failed(monkeypatch, notified, error):
    marked = charge_failing_with(monkeypatch, error)

    asyncio.run(auto_top_up_charging.check("company", "acme"))

    assert notified == []
    assert marked == []
