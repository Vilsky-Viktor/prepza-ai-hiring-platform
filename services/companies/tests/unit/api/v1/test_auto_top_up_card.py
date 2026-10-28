"""Updating an automatic top-up's card from the company's billing: owners and admins open the
checkout billing makes (counted against the checkout limit); a viewer never reaches billing."""

import pytest
from fastapi import HTTPException

from companies.api.v1 import billing as billing_routes
from companies.integrations import billing_prices
from companies.main import app
from tests.unit.api.v1.test_billing_page import COMPANY, COMPANY_ID, as_member

CARD = f"{COMPANY}/auto-top-up/card"


@pytest.fixture
def billing(monkeypatch):
    """What billing was asked for, and what was counted against the limit."""
    seen = {"asked": [], "counted": []}

    async def card(company_id, buyer_id):
        seen["asked"].append((company_id, buyer_id))

        return "txn_card"

    async def count(redis, key, name, **whose):
        seen["counted"].append((key, name))

    monkeypatch.setattr(billing_prices, "update_auto_top_up_card", card)
    monkeypatch.setattr(billing_routes, "hit_or_skip", count)

    return seen


def test_an_admin_gets_the_checkout_that_saves_a_new_card(client, monkeypatch, billing):
    as_member(monkeypatch, "admin")

    response = client.post(CARD)
    app.dependency_overrides.clear()

    assert response.json() == {"transaction_id": "txn_card"}
    assert billing["asked"] == [(COMPANY_ID, "bob")]
    assert billing["counted"] == [("rate:checkout-calls:bob", "CHECKOUT_CALLS_PER_USER_HOUR")]


def test_a_viewer_cant_update_the_card(client, monkeypatch, billing):
    as_member(monkeypatch, "viewer")

    response = client.post(CARD)
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert billing == {"asked": [], "counted": []}


def test_past_the_checkout_limit_billing_isnt_asked(client, monkeypatch, billing):
    async def over(redis, key, name, **whose):
        raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(billing_routes, "hit_or_skip", over)
    as_member(monkeypatch, "owner")

    response = client.post(CARD)
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert billing["asked"] == []
