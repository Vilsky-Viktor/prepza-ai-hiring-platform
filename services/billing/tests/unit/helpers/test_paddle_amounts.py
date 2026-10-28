"""Every currency billing sells in is one Paddle charges in, priced in whole minor units as
Paddle counts them, and every top-up is above Paddle's minimum charge there."""

import pytest

from billing.constants.currencies import Currency
from billing.constants.products import CUSTOM_TOP_UP_MAX, TOP_UPS
from billing.helpers.credits import candidate_tiers, custom_top_up, top_up_price
from billing.services.catalog import candidates_price

# Paddle's minimum payment (minor units) per currency, as its API's
# GET /currencies gave them on 2026-10-21 (sandbox and live share them). A new currency is
# checked there first and added here.
PADDLE_MINIMUMS = {
    Currency.USD: 70,
    Currency.EUR: 65,
    Currency.GBP: 55,
    Currency.CAD: 100,
    Currency.AUD: 110,
    Currency.ILS: 250,
    Currency.PLN: 265,
    Currency.JPY: 100,
    Currency.KRW: 980,
    Currency.TWD: 2500,
    Currency.HKD: 550,
    Currency.CHF: 60,
    Currency.THB: 2300,
    Currency.SGD: 90,
    Currency.INR: 6000,
}


def test_every_currency_sold_was_checked_against_paddle():
    assert set(PADDLE_MINIMUMS) == set(Currency)


@pytest.mark.parametrize("currency", list(Currency))
def test_prices_are_whole_minor_units_above_paddles_minimum(currency):
    minimum = PADDLE_MINIMUMS[currency]
    tiers = candidate_tiers(currency)
    smallest_count, _ = tiers[0]
    smallest = custom_top_up(smallest_count, currency)

    assert all(isinstance(cents, int) and cents > 0 for _, cents in tiers)
    assert smallest[0] * smallest[1] >= minimum
    assert all(top_up_price(top_up, currency) >= minimum for top_up in TOP_UPS)


@pytest.mark.parametrize("currency", list(Currency))
@pytest.mark.parametrize("candidates", [10, 49, 333, CUSTOM_TOP_UP_MAX])
def test_the_amount_paddle_is_sent_is_an_integer_string(currency, candidates):
    count, cents = custom_top_up(candidates, currency)
    amount = candidates_price(count, cents, currency, None, "en")["unit_price"]["amount"]

    assert amount.isdigit()
    assert int(amount) == count * cents
