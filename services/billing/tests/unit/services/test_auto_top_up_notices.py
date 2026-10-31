from datetime import UTC, datetime
from types import SimpleNamespace

from testee_common.events.notifications import notification

from billing.services.auto_top_up_notices import turned_on

NOW = datetime(2026, 10, 30, tzinfo=UTC)


def row(**values):
    agreed = {
        "owner_type": "company",
        "owner_id": "acme",
        "product": "topup_50",
        "threshold": 1_500,
        "currency": "EUR",
        "price": 5_000,
        "price_currency": "EUR",
        "next_price": None,
        "next_price_from": None,
    }

    return SimpleNamespace(**(agreed | values))


def test_turning_it_on_says_what_each_charge_costs_and_when_once_per_subscription():
    assert turned_on(row(), "sub_01", NOW) == notification(
        "company",
        "acme",
        "auto_top_up_on",
        "/companies/acme/billing",
        key="sub_01",
        price=5_000,
        currency="EUR",
        threshold=1_500,
    )


def test_a_card_saved_in_another_currency_tells_the_price_it_charges_in_that_one():
    # Paddle's checkout was in USD: the price list's price in USD, as each charge costs.
    notice = turned_on(row(currency="USD"), "sub_01", NOW)

    assert (notice["data"]["price"], notice["data"]["currency"]) == (5_000, "USD")
