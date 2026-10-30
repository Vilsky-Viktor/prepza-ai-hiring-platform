import asyncio

import httpx
import pytest

from billing.integrations import paddle
from billing.repositories import auto_top_ups as auto_top_up_rows
from billing.services import auto_top_ups, webhooks


def updated(scheduled_change, subscription_id="sub_01"):
    """Paddle's subscription.updated: its customer cancelled through Paddle's email link or
    portal, which Paddle schedules for the end of the billing period."""
    return {
        "event_type": "subscription.updated",
        "data": {"id": subscription_id, "status": "active", "scheduled_change": scheduled_change},
    }


CANCEL = {"action": "cancel", "effective_at": "2026-11-30T00:00:00Z", "resume_at": None}


@pytest.fixture
def paddle_calls(monkeypatch):
    """What billing asks of Paddle and of the database, for the one subscription it knows."""
    calls = []

    async def owner_of(session, subscription_id):
        return ("company", "acme") if subscription_id == "sub_01" else None

    async def cancel(subscription_id):
        calls.append(("cancelled", subscription_id))

    async def remove_subscription(session, subscription_id):
        calls.append(("off", subscription_id))

    monkeypatch.setattr(auto_top_up_rows, "owner_of", owner_of)
    monkeypatch.setattr(auto_top_up_rows, "remove_subscription", remove_subscription)
    monkeypatch.setattr(paddle, "cancel", cancel)

    return calls


def test_a_cancel_in_paddle_ends_it_at_once_not_at_the_periods_end(paddle_calls):
    asyncio.run(webhooks.handle(updated(CANCEL)))

    # Cancelled in Paddle first, so a failure leaves it on to be tried again.
    assert paddle_calls == [("cancelled", "sub_01"), ("off", "sub_01")]


@pytest.mark.parametrize(
    "event",
    [
        updated(None),
        updated({"action": "pause", "effective_at": "2026-11-30T00:00:00Z"}),
        updated(CANCEL, subscription_id="sub_someone_elses"),
    ],
)
def test_other_changes_and_subscriptions_billing_doesnt_know_change_nothing(paddle_calls, event):
    asyncio.run(webhooks.handle(event))

    assert paddle_calls == []


def test_paddle_failing_to_cancel_leaves_it_on_for_paddle_to_send_again(monkeypatch, paddle_calls):
    request = httpx.Request("POST", "https://paddle.test")

    async def cancel(subscription_id):
        raise httpx.HTTPStatusError(
            "", request=request, response=httpx.Response(503, request=request)
        )

    async def still_active(subscription_id):
        return "active"

    monkeypatch.setattr(paddle, "cancel", cancel)
    monkeypatch.setattr(paddle, "subscription_status", still_active)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(auto_top_ups.cancel_scheduled(updated(CANCEL)["data"]))

    assert paddle_calls == []
