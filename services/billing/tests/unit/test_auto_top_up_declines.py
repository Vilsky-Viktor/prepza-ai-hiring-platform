"""An automatic charge Paddle refuses: a declined card counts and the company is told, tried again
a few times at most, or paused at once when the decline can't pass later; Paddle refusing billing
itself (its key, a permission, its rate limit) is never told as the card's."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.notifications import notification

from app.integrations import paddle
from app.services import auto_top_up_declines, auto_top_ups
from app.storage import auto_top_up_charges
from app.storage import auto_top_ups as rows

ROW = SimpleNamespace(subscription_id="sub_01", product="topup_50", currency="USD")
FAILED = notification("company", "acme", "auto_top_up_failed", "/top-up")


def refused(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://sandbox-api.paddle.com/subscriptions/sub_01/charge")

    return httpx.HTTPStatusError(
        "refused", request=request, response=httpx.Response(status, request=request)
    )


@pytest.fixture
def charging(monkeypatch):
    """A running automatic top-up whose charge Paddle refuses with a status; how many declines
    in a row the storage counts before pausing it, Paddle's error code for the decline, and
    what happened: declines counted, pauses and notifications."""
    seen = {"declines": [], "paused": [], "told": []}
    setup = {"pauses_at": None, "code": None, "read_fails": False}

    async def claim_charge(owner_type, owner_id, now):
        return ROW

    async def declined(owner_type, owner_id, now):
        seen["declines"].append(owner_id)

        return len(seen["declines"]) == setup["pauses_at"]

    async def pause(owner_type, owner_id, now):
        seen["paused"].append(owner_id)

        return True

    async def charge_error(subscription_id, since, timeout):
        if setup["read_fails"]:
            raise httpx.ReadTimeout("slow")

        return setup["code"]

    async def tell(event):
        seen["told"].append(event)

    async def nothing():
        pass

    def answer(status):
        async def charge(row, owner_id, now):
            raise refused(status)

        monkeypatch.setattr(auto_top_ups, "charge", charge)

    monkeypatch.setattr(rows, "claim_charge", claim_charge)
    monkeypatch.setattr(auto_top_up_charges, "declined", declined)
    monkeypatch.setattr(auto_top_up_charges, "pause", pause)
    monkeypatch.setattr(paddle, "charge_error", charge_error)
    monkeypatch.setattr(auto_top_up_declines, "tell", tell)
    monkeypatch.setattr(auto_top_up_declines.outbox_service, "flush_quietly", nothing)

    return answer, setup, seen


def paused_notice(event):
    return (event["kind"], event["link"], event["key"].startswith("auto_top_up_paused:acme:"))


@pytest.mark.parametrize("status", [400, 402, 422])
def test_a_soft_decline_counts_and_the_company_is_told_it_will_be_tried_again(charging, status):
    answer, setup, seen = charging
    answer(status)
    setup["code"] = "not_enough_balance"

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert seen["declines"] == ["acme"]
    assert seen["paused"] == []
    assert seen["told"] == [FAILED]


@pytest.mark.parametrize(
    "code",
    [
        "declined_not_retryable",
        "blocked_card",
        "fraud",
        "expired_card",
        "invalid_payment_details",
        "authentication_failed",
        "transaction_not_permitted",
    ],
)
def test_a_hard_decline_pauses_at_once_and_says_to_update_the_card(charging, code):
    answer, setup, seen = charging
    answer(400)
    setup["code"] = code

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert seen["declines"] == ["acme"]
    assert seen["paused"] == ["acme"]
    assert [paused_notice(event) for event in seen["told"]] == [
        ("auto_top_up_paused", "/companies/acme/billing", True)
    ]


def test_the_last_soft_decline_pauses_without_reading_the_code(charging):
    answer, setup, seen = charging
    answer(400)
    setup["pauses_at"] = 1
    setup["code"] = "fraud"

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert seen["paused"] == []
    assert [paused_notice(event) for event in seen["told"]] == [
        ("auto_top_up_paused", "/companies/acme/billing", True)
    ]


@pytest.mark.parametrize(("code", "read_fails"), [(None, False), ("unknown", False), (None, True)])
def test_a_decline_whose_reason_isnt_known_counts_as_one_that_may_pass(charging, code, read_fails):
    answer, setup, seen = charging
    answer(400)
    setup["code"] = code
    setup["read_fails"] = read_fails

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert seen["paused"] == []
    assert seen["told"] == [FAILED]


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_paddle_refusing_billing_isnt_the_companys_card(charging, status):
    answer, _, seen = charging
    answer(status)

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert seen == {"declines": [], "paused": [], "told": []}
