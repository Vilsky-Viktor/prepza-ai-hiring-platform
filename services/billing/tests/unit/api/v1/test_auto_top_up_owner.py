import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from billing.constants.products import (
    AGREEMENT_NEEDED,
    AUTO_TOP_UP_THRESHOLDS,
    NOT_YOUR_AUTO_TOP_UP,
)
from billing.repositories import auto_top_ups, company_actions
from billing.services import auto_top_ups as service

URL = f"/companies/{uuid.uuid4()}/auto-top-up"
CHOICE = {"product": "topup_1000", "threshold": AUTO_TOP_UP_THRESHOLDS[-1], "agreed": True}


class Saved(list):
    """What was saved, with the row as it is now."""

    row = None


@pytest.fixture
def running(monkeypatch, editor):
    """The company's automatic top-up runs on Ann's card; returns what was saved."""
    saved = Saved()
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
        agreed_at=None,
    )
    saved.row = row

    async def get(session, owner_type, owner_id):
        return row

    async def save(
        session,
        owner_type,
        owner_id,
        product,
        threshold,
        buyer_id,
        price,
        currency,
        agreed_at,
        language,
    ):
        saved.append((product, threshold, buyer_id, price, currency, language))
        row.agreed_at = agreed_at
        row.product, row.threshold, row.price = product, threshold, price

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


@pytest.mark.parametrize("agreed", [False, None])
def test_saving_it_needs_the_buyers_tick(client, editor, running, agreed):
    editor("ann")
    body = {key: value for key, value in CHOICE.items() if key != "agreed"}

    if agreed is not None:
        body["agreed"] = agreed

    response = client.put(URL, json=body)

    assert response.status_code == 422
    assert response.json() == {"detail": AGREEMENT_NEEDED}
    assert running == []


def test_the_action_log_keeps_who_when_and_the_terms_agreed_to(
    client, editor, running, monkeypatch
):
    logged = []
    monkeypatch.setattr(company_actions, "log", lambda *args: logged.append(args))
    editor("ann")
    before = datetime.now(UTC)

    client.put(URL, json=CHOICE)

    [(_, _, user, action, terms)] = logged
    assert (user, action) == ("ann", "auto_top_up_changed")
    # The price and the level agreed to, as Ann's language writes them.
    assert terms == "$1,000 plus tax when the balance falls under 2,500 credits"
    assert before <= running.row.agreed_at <= datetime.now(UTC)
