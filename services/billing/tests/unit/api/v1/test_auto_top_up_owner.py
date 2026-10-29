import uuid
from types import SimpleNamespace

import pytest

from billing.constants.products import AUTO_TOP_UP_THRESHOLDS, NOT_YOUR_AUTO_TOP_UP
from billing.repositories import auto_top_ups
from billing.services import auto_top_ups as service

URL = f"/companies/{uuid.uuid4()}/auto-top-up"
CHOICE = {"product": "topup_1000", "threshold": AUTO_TOP_UP_THRESHOLDS[-1]}


@pytest.fixture
def running(monkeypatch, editor):
    """The company's automatic top-up runs on Ann's card; returns what was saved."""
    saved = []
    row = SimpleNamespace(
        subscription_id="sub_1",
        buyer_id="ann",
        product="topup_50",
        threshold=AUTO_TOP_UP_THRESHOLDS[0],
        failed_at=None,
        currency="USD",
        paused_at=None,
        price=5000,
        price_currency="USD",
        next_price=None,
        next_price_from=None,
    )

    async def get(session, owner_type, owner_id):
        return row

    async def save(
        session, owner_type, owner_id, product, threshold, buyer_id, price, currency, language
    ):
        saved.append((product, threshold, buyer_id, price, currency, language))

        return row

    monkeypatch.setattr(service, "offered", lambda: True)
    monkeypatch.setattr(service, "products", lambda: ["topup_50", "topup_1000"])
    monkeypatch.setattr(auto_top_ups, "get", get)
    monkeypatch.setattr(auto_top_ups, "save", save)

    return saved


def test_another_member_cant_change_a_top_up_charged_to_someone_elses_card(client, editor, running):
    editor("bob")
    response = client.put(URL, json=CHOICE)

    assert response.status_code == 403
    assert response.json() == {"detail": NOT_YOUR_AUTO_TOP_UP}
    assert running == []


def test_the_cards_owner_changes_it(client, editor, running):
    editor("ann")
    response = client.put(URL, json=CHOICE, headers={"Accept-Language": "de"})

    assert response.status_code == 200
    # At the price list's price for the top-up chosen, in the company's currency; each charge
    # named in Ann's interface language.
    assert running == [("topup_1000", AUTO_TOP_UP_THRESHOLDS[-1], "ann", 100_000, "USD", "de")]


def test_without_a_language_charges_are_named_in_english(client, editor, running):
    editor("ann")
    client.put(URL, json=CHOICE)

    assert running[0][-1] == "en"
