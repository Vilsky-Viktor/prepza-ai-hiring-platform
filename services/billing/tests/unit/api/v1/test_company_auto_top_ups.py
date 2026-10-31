"""A company's automatic top-up in billing: any member sees it, owners and admins set it up,
change it, turn it off and update its card, as themselves (who goes to the action log)."""

import uuid

import httpx
import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.http import http

from billing.main import app
from billing.schemas.billing import AutoTopUpOut, CheckoutOut
from billing.services import auto_top_up_declines, auto_top_ups, checkout_calls
from tests.unit.api.v1.test_company_payments import ROLES

COMPANY_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}/auto-top-up"
OFF = AutoTopUpOut(
    offered=True,
    on=False,
    waiting=False,
    product=None,
    threshold=None,
    products=["topup_50"],
    thresholds=[500],
    currency="USD",
    prices={"topup_50": 5000},
)


@pytest.fixture
def calls(monkeypatch):
    """Companies answers who's who (test_company_payments.ROLES); billing's own steps recorded."""
    recorded = []

    def answer(request):
        return httpx.Response(200, json=ROLES[request.url.params["user_id"]])

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    async def out(owner_type, owner_id, currency):
        recorded.append(("out", owner_id, currency))

        return OFF

    async def turn_on(owner_type, owner_id, body, buyer_id, currency, language, logged):
        recorded.append(("on", owner_id, body.product, buyer_id, language, logged))

        return OFF

    async def turn_off(owner_type, owner_id, buyer_id=None, actor=None):
        recorded.append(("off", owner_id, actor))

    async def card_update(owner_type, owner_id, buyer_id):
        recorded.append(("card", owner_id, buyer_id))

        return CheckoutOut(transaction_id="txn_card")

    async def counted(redis, key, name, **whose):
        recorded.append(("counted", key))

    monkeypatch.setattr(auto_top_ups, "out", out)
    monkeypatch.setattr(auto_top_ups, "turn_on", turn_on)
    monkeypatch.setattr(auto_top_ups, "turn_off", turn_off)
    monkeypatch.setattr(auto_top_up_declines, "card_update", card_update)
    monkeypatch.setattr(checkout_calls, "hit_or_skip", counted)

    yield recorded

    app.dependency_overrides.clear()


def sign_in(user_id):
    app.dependency_overrides[current_user] = lambda: User(
        uid=user_id, email=f"{user_id}@example.com", email_verified=True
    )


def test_an_owner_sets_it_up_turns_it_off_and_updates_the_card_as_themselves(client, calls):
    company = str(COMPANY_ID)
    sign_in("owner")

    on = client.put(
        URL, json={"product": "topup_50", "threshold": 500}, headers={"Accept-Language": "pl"}
    )
    off = client.delete(URL)
    card = client.post(f"{URL}/card")

    assert (on.status_code, off.status_code) == (200, 204)
    assert card.json() == {"transaction_id": "txn_card"}
    assert calls == [
        ("counted", "rate:checkout-calls:owner"),
        ("on", company, "topup_50", "owner", "pl", True),
        ("off", company, "owner"),
        ("counted", "rate:checkout-calls:owner"),
        ("card", company, "owner"),
    ]


def test_a_viewer_sees_it_and_changes_nothing_and_a_stranger_sees_nothing(client, calls):
    sign_in("viewer")

    seen = client.get(URL, headers={"X-Client-Country": "DE"})
    changes = [
        client.put(URL, json={"product": "topup_50", "threshold": 500}).status_code,
        client.delete(URL).status_code,
        client.post(f"{URL}/card").status_code,
    ]
    sign_in("stranger")
    stranger = client.get(URL)

    assert seen.json()["offered"] is True
    assert changes == [403, 403, 403]
    assert stranger.status_code == 404
    # The viewer's look, priced in the visitor's country's currency (none saved yet).
    assert calls == [("out", str(COMPANY_ID), "EUR")]
