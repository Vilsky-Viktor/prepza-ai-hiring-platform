"""Which currency prices are in: a company's billing in the company's, elsewhere the signed-in
person's, signed out the visitor's country's. A company's or a person's is saved from the first
known country billing sees them with; without a country (calls from AI apps, the public API,
other services, tests) the saved one applies, or US dollars, and nothing is saved."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from billing.constants.currencies import Currency
from billing.repositories import auto_top_ups
from tests.unit.api.v1.test_internal import AUTH

COMPANY = "/internal/companies/acme"


@pytest.fixture
def no_auto_top_up(monkeypatch):
    async def none(owner_type, owner_id):
        return None

    monkeypatch.setattr(auto_top_ups, "get", none)


@pytest.mark.parametrize(
    ("saved", "country", "shown", "kept"),
    [
        # Nothing saved and no country: US dollars, nothing saved.
        (None, None, "USD", None),
        (None, "XX", "USD", None),
        # Nothing saved yet: the country's, saved from now on.
        (None, "GB", "GBP", "GBP"),
        # Saved: kept, wherever the person is, with a country or without.
        ("EUR", None, "EUR", "EUR"),
        ("EUR", "US", "EUR", "EUR"),
    ],
)
def test_a_signed_in_persons_prices_are_in_their_saved_currency(
    client, signed_in, saved_currencies, saved, country, shown, kept
):
    if saved:
        saved_currencies[("user", "bob@example.com")] = saved

    signed_in("bob@example.com")
    params = {"country": country} if country else {}

    assert client.get("/catalog", params=params).json()["currency"] == shown
    assert client.get("/me/currency", params=params).json() == {
        "currency": shown,
        "currencies": [currency.value for currency in Currency],
    }
    assert saved_currencies.get(("user", "bob@example.com")) == kept


def test_a_person_changes_their_currency(client, signed_in, saved_currencies):
    signed_in("bob@example.com")

    response = client.put("/me/currency", json={"currency": "GBP"})
    refused = client.put("/me/currency", json={"currency": "XYZ"})

    assert response.json()["currency"] == "GBP"
    assert refused.status_code == 422
    assert saved_currencies == {("user", "bob@example.com"): "GBP"}


@pytest.mark.parametrize(("country", "kept"), [(None, None), ("NO", "EUR")])
def test_a_new_accounts_currency_is_saved_only_with_a_country(
    client, saved_currencies, country, kept
):
    params = {"country": country} if country else {}

    response = client.post("/internal/users/ann/currency", params=params, headers=AUTH)

    assert response.status_code == 204
    assert saved_currencies.get(("user", "ann")) == kept


@pytest.mark.parametrize(
    ("saved", "country", "shown"),
    [(None, None, "USD"), (None, "DE", "EUR"), ("GBP", None, "GBP"), ("GBP", "US", "GBP")],
)
def test_a_companys_prices_are_in_its_currency_with_or_without_a_country(
    client, saved_currencies, no_auto_top_up, saved, country, shown
):
    if saved:
        saved_currencies[("company", "acme")] = saved

    params = {"country": country} if country else {}
    catalog = client.get(f"{COMPANY}/catalog", params=params, headers=AUTH)
    currency = client.get(f"{COMPANY}/currency", params=params, headers=AUTH)
    auto_top_up = client.get(f"{COMPANY}/auto-top-up", params=params, headers=AUTH)

    assert catalog.json()["currency"] == shown
    assert currency.json()["currency"] == shown
    assert auto_top_up.json()["currency"] == shown


def test_a_company_is_welcomed_with_or_without_its_owners_country(
    client, monkeypatch, saved_currencies
):
    async def welcomed(company_id, owner_email):
        return False

    monkeypatch.setattr("billing.repositories.ledger.welcome_company", welcomed)

    for company, country in (("acme", None), ("beta", "IE")):
        body = {"owner_email": "ann@example.com", **({"country": country} if country else {})}
        response = client.post(f"/internal/companies/{company}/welcome", json=body, headers=AUTH)
        assert response.status_code == 204

    assert saved_currencies == {("company", "beta"): "EUR"}


@pytest.mark.parametrize(
    ("row", "charges"),
    [
        # No automatic top-up: nothing to say.
        (None, None),
        # One waiting for its card charges nothing yet.
        (SimpleNamespace(subscription_id=None), None),
        # A running one, agreed at $45: chosen in euros, it charges the price list's €50 at once.
        (
            SimpleNamespace(
                subscription_id="sub_1",
                product="topup_50",
                price=4500,
                price_currency="USD",
                next_price=None,
                next_price_from=None,
            ),
            5000,
        ),
    ],
)
def test_a_company_changes_its_currency_and_hears_what_automatic_top_up_now_charges(
    client, monkeypatch, saved_currencies, row, charges
):
    async def get(owner_type, owner_id):
        return row

    monkeypatch.setattr(auto_top_ups, "get", get)

    response = client.put(f"{COMPANY}/currency", json={"currency": "EUR"}, headers=AUTH)

    assert response.json() == {
        "currency": "EUR",
        "currencies": [currency.value for currency in Currency],
        "auto_top_up_price": charges,
    }
    assert saved_currencies == {("company", "acme"): "EUR"}


@pytest.mark.parametrize(
    ("subscription", "company", "switched", "charged"),
    [
        # Set up in dollars, the company now in euros: switched over, then charged €50.
        ("USD", "EUR", ["EUR"], ("5000", "EUR")),
        # Already in the company's: charged as it is.
        ("GBP", "GBP", [], ("4000", "GBP")),
        # From before currencies (none recorded) and none saved: dollars as before.
        (None, None, [], ("5000", "USD")),
    ],
)
def test_an_automatic_top_up_charges_in_the_companys_currency(
    monkeypatch, saved_currencies, subscription, company, switched, charged
):
    import asyncio

    from billing.integrations import paddle
    from billing.services import auto_top_ups as service

    if company:
        saved_currencies[("company", "acme")] = company

    row = SimpleNamespace(
        subscription_id="sub_1",
        product="topup_50",
        currency=subscription,
        price=None,
        price_currency=None,
        language=None,
    )
    patched, recorded, items = [], [], []

    async def set_currency(subscription_id, currency):
        patched.append(currency)

    async def record(subscription_id, currency):
        recorded.append(currency)

    async def charge(subscription_id, price):
        items.append((price["unit_price"]["amount"], price["unit_price"]["currency_code"]))

    monkeypatch.setattr(paddle, "set_currency", set_currency)
    monkeypatch.setattr(paddle, "charge", charge)
    monkeypatch.setattr(auto_top_ups, "set_currency", record)

    asyncio.run(service.charge(row, "acme", datetime.now(UTC)))

    assert patched == recorded == switched
    assert items == [charged]
