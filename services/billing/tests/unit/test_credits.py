import pytest

from app.constants.currencies import Currency
from app.constants.products import TOP_UPS
from app.helpers.credits import custom_top_up, top_up_price

# Each currency's own round prices per candidate, from 10, 50, 200 and 500 candidates.
PRICES = {
    Currency.USD: [500, 400, 300, 200],
    Currency.EUR: [500, 400, 300, 200],
    Currency.GBP: [400, 300, 225, 150],
    Currency.CAD: [700, 550, 400, 275],
    Currency.AUD: [750, 600, 450, 300],
    Currency.ILS: [1800, 1500, 1100, 750],
    Currency.PLN: [1800, 1500, 1100, 750],
    # Whole yen and won: Paddle counts them without decimals.
    Currency.JPY: [750, 600, 450, 300],
    Currency.KRW: [7000, 5500, 4000, 2750],
    Currency.TWD: [16000, 13000, 9500, 6500],
    Currency.HKD: [4000, 3100, 2300, 1600],
    Currency.CHF: [450, 350, 260, 175],
    Currency.THB: [17000, 13500, 10000, 7000],
    Currency.SGD: [650, 530, 400, 265],
    Currency.INR: [42000, 34000, 25000, 17000],
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
        # Each currency's steps come from its own prices.
        (Currency.CAD, 145, (145, 550)),
        (Currency.CAD, 146, (200, 400)),
        (Currency.CAD, 344, (500, 275)),
        (Currency.ILS, 41, (41, 1800)),
        (Currency.ILS, 42, (50, 1500)),
        (Currency.AUD, 333, (333, 450)),
        (Currency.AUD, 334, (500, 300)),
        (Currency.JPY, 39, (39, 750)),
        (Currency.JPY, 40, (50, 600)),
        (Currency.HKD, 348, (500, 1600)),
        (Currency.THB, 350, (500, 7000)),
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
        # Switzerland has its own; Liechtenstein keeps the euro.
        ("CH", "CHF", [4_500, 17_500, 52_000, 87_500], 175, 450),
        ("LI", "EUR", [5_000, 20_000, 60_000, 100_000], 200, 500),
        ("JP", "JPY", [7_500, 30_000, 90_000, 150_000], 300, 750),
        ("KR", "KRW", [70_000, 275_000, 800_000, 1_375_000], 2_750, 7_000),
        ("TW", "TWD", [160_000, 650_000, 1_900_000, 3_250_000], 6_500, 16_000),
        ("HK", "HKD", [40_000, 155_000, 460_000, 800_000], 1_600, 4_000),
        ("TH", "THB", [170_000, 675_000, 2_000_000, 3_500_000], 7_000, 17_000),
        ("SG", "SGD", [6_500, 26_500, 80_000, 132_500], 265, 650),
        ("IN", "INR", [420_000, 1_700_000, 5_000_000, 8_500_000], 17_000, 42_000),
        ("GB", "GBP", [4_000, 15_000, 45_000, 75_000], 150, 400),
        ("CA", "CAD", [7_000, 27_500, 80_000, 137_500], 275, 700),
        ("AU", "AUD", [7_500, 30_000, 90_000, 150_000], 300, 750),
        ("IL", "ILS", [18_000, 75_000, 220_000, 375_000], 750, 1_800),
        # Ukraine has none of its own: US dollars.
        ("UA", "USD", [5_000, 20_000, 60_000, 100_000], 200, 500),
        # Poland has its own, not the euro.
        ("PL", "PLN", [18_000, 75_000, 220_000, 375_000], 750, 1_800),
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
