import pytest

from app.constants.currencies import Currency
from app.constants.products import TOP_UPS
from app.helpers.credits import custom_top_up, top_up_price

# Each currency's own round prices per candidate, from 10, 50, 200 and 500 candidates.
PRICES = {
    Currency.USD: [500, 400, 300, 200],
    Currency.EUR: [500, 400, 300, 200],
    Currency.GBP: [400, 300, 225, 150],
}


@pytest.mark.parametrize("currency", list(Currency))
def test_each_fixed_top_up_buys_its_candidates_at_its_currencys_price(currency):
    assert [top_up_price(product, currency) for product in TOP_UPS] == [
        candidates * cents
        for candidates, cents in zip((10, 50, 200, 500), PRICES[currency], strict=True)
    ]


@pytest.mark.parametrize(
    ("currency", "chosen", "bought"),
    [
        (Currency.USD, 39, (39, 500)),
        # 40 at $5 would cost what 50 at $4 cost: those 50.
        (Currency.USD, 40, (50, 400)),
        (Currency.EUR, 40, (50, 400)),
        # In pounds the next level is cheaper sooner: 38 at £4 cost more than 50 at £3.
        (Currency.GBP, 37, (37, 400)),
        (Currency.GBP, 38, (50, 300)),
        (Currency.GBP, 333, (333, 225)),
        (Currency.GBP, 334, (500, 150)),
        (Currency.GBP, 1_000, (1_000, 150)),
        (Currency.GBP, 1_001, None),
    ],
)
def test_a_custom_top_up_moves_up_where_the_next_level_costs_no_more(currency, chosen, bought):
    assert custom_top_up(chosen, currency) == bought


@pytest.mark.parametrize(
    ("country", "currency", "prices", "low", "high"),
    [
        (None, "USD", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("US", "USD", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("de", "EUR", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("CH", "EUR", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("GB", "GBP", [4_000, 15_000, 45_000, 75_000], 150, 400),
        # An unknown or malformed country is as none.
        ("XX", "USD", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("Germany", "USD", [5_000, 20_000, 60_000, 100_000], 200, 500),
    ],
)
def test_a_signed_out_visitor_sees_their_countrys_prices(
    client, saved_currencies, country, currency, prices, low, high
):
    catalog = client.get("/catalog", params={"country": country} if country else {}).json()

    assert catalog["currency"] == currency
    assert [product["price_cents"] for product in catalog["products"]] == prices
    assert (catalog["candidate_cents_min"], catalog["candidate_cents_max"]) == (low, high)
    assert catalog["free_candidates"] == 3
    # Nothing is saved for someone signed out.
    assert saved_currencies == {}


def test_the_volume_prices_say_from_which_amount_they_apply(client):
    prices = client.get("/catalog", params={"country": "GB"}).json()["candidate_prices"]

    assert prices == [
        {"from_cents": 4_000, "cents": 400},
        {"from_cents": 15_000, "cents": 300},
        {"from_cents": 45_000, "cents": 225},
        {"from_cents": 75_000, "cents": 150},
    ]
