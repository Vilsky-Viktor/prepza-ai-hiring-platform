"""A paused automatic top-up's card: only the person whose card pays opens the checkout that
saves a new one, and Paddle saving it resumes the top-up; what the company sees meanwhile."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.http import bearer

from app.constants.products import NOT_YOUR_AUTO_TOP_UP
from app.integrations import paddle
from app.service_auth import service_token
from app.services import auto_top_up_declines, auto_top_ups, webhooks
from app.storage import auto_top_up_charges
from app.storage import auto_top_ups as rows
from tests.unit.paddle_events import completed

AUTH = bearer(service_token("billing"))
CARD = "/internal/companies/acme/auto-top-up/card"
SAVED_AT = "2026-10-21T15:30:00.000000Z"


def running(**overrides):
    values = {
        "subscription_id": "sub_1",
        "buyer_id": "ann",
        "product": "topup_50",
        "threshold": 500,
        "paused_at": datetime(2026, 10, 20, tzinfo=UTC),
        "price": 4500,
        "price_currency": "USD",
        "next_price": None,
        "next_price_from": None,
    }

    return SimpleNamespace(**{**values, **overrides})


@pytest.fixture
def stored(monkeypatch):
    """The company's automatic top-up as billing has it (none until set)."""
    found = {"row": None}

    async def get(owner_type, owner_id):
        return found["row"]

    async def update_transaction(subscription_id):
        return f"txn_card_{subscription_id}"

    monkeypatch.setattr(rows, "get", get)
    monkeypatch.setattr(paddle, "card_update_transaction", update_transaction)

    return found


@pytest.mark.parametrize(
    ("row", "buyer", "status", "answer"),
    [
        (running(), "ann", 200, {"transaction_id": "txn_card_sub_1"}),
        (running(), "bob", 403, {"detail": NOT_YOUR_AUTO_TOP_UP}),
        (running(subscription_id=None), "ann", 409, {"detail": auto_top_up_declines.NOT_RUNNING}),
        (None, "ann", 409, {"detail": auto_top_up_declines.NOT_RUNNING}),
    ],
)
def test_only_the_cards_owner_gets_the_checkout_that_saves_a_new_card(
    client, stored, row, buyer, status, answer
):
    stored["row"] = row

    response = client.post(CARD, params={"buyer_id": buyer}, headers=AUTH)

    assert response.status_code == status
    assert response.json() == answer


def test_a_card_update_needs_billings_caller(client, stored):
    assert client.post(CARD, params={"buyer_id": "ann"}).status_code in (401, 403)


@pytest.mark.parametrize(("resumed", "checked"), [(("company", "acme"), ["acme"]), (None, [])])
def test_paddle_saving_the_new_card_resumes_it_and_grants_nothing(monkeypatch, resumed, checked):
    """A repeated web hook, or one for a top-up paused again since, resumes nothing."""
    asked, charged, granted = [], [], []

    async def resume(subscription_id, saved_at):
        asked.append((subscription_id, saved_at))

        return resumed

    async def check(owner_type, owner_id):
        charged.append(owner_id)

    async def grant(*args):
        granted.append(args)

    monkeypatch.setattr(auto_top_up_charges, "resume", resume)
    monkeypatch.setattr(auto_top_ups, "check", check)
    monkeypatch.setattr("app.storage.purchases.grant", grant)
    event = completed()
    event["data"].update(
        origin="subscription_payment_method_change", subscription_id="sub_1", created_at=SAVED_AT
    )

    asyncio.run(webhooks.handle(event))

    assert asked == [("sub_1", datetime(2026, 10, 21, 15, 30, tzinfo=UTC))]
    assert charged == checked
    assert granted == []


@pytest.mark.parametrize(
    ("row", "paused", "price", "coming"),
    [
        # Paused: said so, at the price agreed.
        (running(), True, 4500, (None, None)),
        # Running with a new price announced: the agreed one now, the new one and its day.
        (
            running(
                paused_at=None, next_price=5000, next_price_from=datetime(2026, 11, 21, tzinfo=UTC)
            ),
            False,
            4500,
            (5000, "2026-11-21T00:00:00Z"),
        ),
    ],
)
def test_the_company_sees_whether_its_paused_and_what_each_charge_costs(
    client, stored, monkeypatch, row, paused, price, coming
):
    stored["row"] = row
    monkeypatch.setattr(auto_top_ups, "offered", lambda: True)

    body = client.get("/internal/companies/acme/auto-top-up", headers=AUTH).json()

    assert body["paused"] is paused
    assert body["prices"]["topup_50"] == price
    assert (body["next_price"], body["next_price_from"]) == coming
