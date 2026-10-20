import asyncio

import pytest

from app.config.settings import settings
from app.constants.products import CANDIDATES_OUT_OF_RANGE, CUSTOM_TOP_UP_MAX
from app.helpers.credits import candidate_tiers, custom_top_up
from app.integrations import paddle
from app.services import adjustments, webhooks
from tests.unit.paddle_events import completed
from tests.unit.test_internal import AUTH
from tests.unit.test_webhooks import granted  # noqa: F401 (fixture)

URL = "/internal/companies/acme/checkout"
PRODUCT = "pro_candidates"


@pytest.fixture(autouse=True)
def product(monkeypatch):
    """Paddle's product for it is set, whatever the local settings have."""
    monkeypatch.setattr(settings, "paddle_product_candidates", PRODUCT)


@pytest.fixture
def made(monkeypatch):
    calls = []

    async def create(price, custom_data):
        calls.append((price, custom_data))

        return "txn_new"

    monkeypatch.setattr(paddle, "create_transaction", create)

    return calls


def paid(candidates, cents, product_id=PRODUCT):
    """Paddle's transaction.completed of billing's checkout for `candidates`, paid `cents`."""
    event = completed(price_id="pri_made_in_the_transaction")
    event["data"]["custom_data"]["candidates"] = candidates
    event["data"]["items"][0]["price"].update(
        product_id=product_id, unit_price={"amount": str(cents), "currency_code": "USD"}
    )

    return event


@pytest.mark.parametrize(
    ("chosen", "bought"),
    [
        (10, (10, 500)),
        (39, (39, 500)),
        # From 40 at $5, the next level's 50 for $200 cost no more.
        (40, (50, 400)),
        (49, (50, 400)),
        (50, (50, 400)),
        (149, (149, 400)),
        (150, (200, 300)),
        (199, (200, 300)),
        (200, (200, 300)),
        (333, (333, 300)),
        (334, (500, 200)),
        (499, (500, 200)),
        (500, (500, 200)),
        (1_000, (1_000, 200)),
        (9, None),
        (1_001, None),
    ],
)
def test_a_count_buys_its_level_or_the_next_one_when_that_costs_no_more(chosen, bought):
    assert custom_top_up(chosen) == bought


def test_the_catalog_gives_the_range_and_each_levels_price(client):
    custom = client.get("/catalog").json()["custom"]

    assert custom == {
        "min_candidates": 10,
        "max_candidates": 1_000,
        "on_sale": True,
        "tiers": [
            {"from_candidates": 10, "cents": 500, "upgrade_from": 40},
            {"from_candidates": 50, "cents": 400, "upgrade_from": 150},
            {"from_candidates": 200, "cents": 300, "upgrade_from": 334},
            {"from_candidates": 500, "cents": 200, "upgrade_from": None},
        ],
    }


def test_without_paddles_product_it_isnt_on_sale(client, made, monkeypatch):
    monkeypatch.setattr(settings, "paddle_product_candidates", "")

    on_sale = client.get("/catalog").json()["custom"]["on_sale"]
    response = client.post(URL, params={"buyer_id": "ann"}, json={"candidates": 60}, headers=AUTH)

    assert on_sale is False
    assert response.status_code == 422
    assert response.json()["detail"] == "This top-up isn't available"
    assert made == []


@pytest.mark.parametrize(
    ("chosen", "candidates", "amount"),
    [(10, 10, "5000"), (45, 50, "20000"), (700, 700, "140000")],
)
def test_billing_makes_one_item_the_buyer_cant_change(client, made, chosen, candidates, amount):
    response = client.post(
        URL, params={"buyer_id": "ann"}, json={"candidates": chosen}, headers=AUTH
    )

    assert response.json() == {"transaction_id": "txn_new"}
    assert made == [
        (
            {
                "name": f"{candidates} candidates",
                "description": f"{candidates} candidates",
                "product_id": PRODUCT,
                "unit_price": {"amount": amount, "currency_code": "USD"},
                "tax_mode": "external",
                "quantity": {"minimum": 1, "maximum": 1},
            },
            {
                "owner_type": "company",
                "owner_id": "acme",
                "buyer_id": "ann",
                "candidates": candidates,
            },
        )
    ]


@pytest.mark.parametrize("chosen", [0, 9, 1_001])
def test_a_count_out_of_range_is_refused(client, made, chosen):
    response = client.post(
        URL, params={"buyer_id": "ann"}, json={"candidates": chosen}, headers=AUTH
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Choose from 10 to 1,000 candidates."
    assert made == []


@pytest.mark.parametrize(
    ("candidates", "cents", "credits"),
    [(10, 5_000, 5_000), (50, 20_000, 25_000), (1_000, 200_000, 500_000)],
)
def test_a_paid_custom_top_up_grants_its_candidates(granted, candidates, cents, credits):  # noqa: F811
    asyncio.run(webhooks.handle(paid(candidates, cents)))

    assert granted == [("txn_01", "candidates", 1, credits, "acme", "ann")]


@pytest.mark.parametrize(
    "event",
    [
        # Another product, a count billing doesn't sell (45 buys 50), none, or out of range.
        paid(50, 20_000, product_id="pro_other"),
        paid(45, 18_000),
        paid(None, 20_000),
        paid(1_001, 200_200),
    ],
)
def test_anything_else_grants_nothing(granted, event):  # noqa: F811
    asyncio.run(webhooks.handle(event))

    assert granted == []


def test_a_refund_takes_back_its_share_of_the_candidates_credits():
    # 50 candidates for $200: $100 back takes back half.
    assert adjustments.share(25_000, "10000", "20000") == 12_500


def test_the_refusal_names_the_range_sold():
    low = candidate_tiers()[0][0]

    assert CANDIDATES_OUT_OF_RANGE == f"Choose from {low:,} to {CUSTOM_TOP_UP_MAX:,} candidates."
