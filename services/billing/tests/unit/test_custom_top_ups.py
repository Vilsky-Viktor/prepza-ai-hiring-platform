import asyncio

import pytest

from app.config.settings import settings
from app.constants.currencies import Currency
from app.constants.products import CANDIDATES_OUT_OF_RANGE, CUSTOM_TOP_UP_MAX
from app.helpers.credits import candidate_tiers
from app.integrations import paddle
from app.services import adjustments, webhooks
from tests.unit.paddle_events import PRODUCT, completed
from tests.unit.test_internal import AUTH
from tests.unit.test_webhooks import granted  # noqa: F401 (fixture)

URL = "/internal/companies/acme/checkout"


@pytest.fixture(autouse=True)
def product(monkeypatch):
    """Paddle's product for it is set, whatever the local settings have."""
    monkeypatch.setattr(settings, "paddle_product_candidates", PRODUCT)


@pytest.fixture
def made(monkeypatch):
    calls = []

    async def create(items, currency, custom_data):
        calls.append((items, currency, custom_data))

        return "txn_new"

    monkeypatch.setattr(paddle, "create_transaction", create)

    return calls


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
    ("country", "saved", "chosen", "candidates", "amount", "currency"),
    [
        # No visitor's country (a call from an AI app or a test) and none saved: US dollars, and
        # nothing is saved.
        (None, None, 10, 10, "5000", "USD"),
        (None, None, 45, 50, "20000", "USD"),
        (None, None, 700, 700, "140000", "USD"),
        # The company's own currency, wherever the buyer is.
        ("DE", "GBP", 38, 50, "15000", "GBP"),
        (None, "EUR", 10, 10, "5000", "EUR"),
        # None saved yet: the visitor's country's, saved from now on.
        ("FR", None, 10, 10, "5000", "EUR"),
    ],
)
def test_billing_makes_one_item_the_buyer_cant_change_in_the_companys_currency(
    client, made, saved_currencies, country, saved, chosen, candidates, amount, currency
):
    if saved:
        saved_currencies[("company", "acme")] = saved

    params = {"buyer_id": "ann", **({"country": country} if country else {})}
    response = client.post(URL, params=params, json={"candidates": chosen}, headers=AUTH)

    assert response.json() == {"transaction_id": "txn_new"}
    item = {
        "name": f"{candidates} candidates",
        "description": f"{candidates} candidates",
        "product_id": PRODUCT,
        "unit_price": {"amount": amount, "currency_code": currency},
        "tax_mode": "external",
        "quantity": {"minimum": 1, "maximum": 1},
        "custom_data": {"candidates": str(candidates)},
    }
    custom = {"owner_type": "company", "owner_id": "acme", "buyer_id": "ann"}
    assert made == [([{"price": item, "quantity": 1}], currency, custom)]
    assert saved_currencies == (
        {("company", "acme"): saved or currency} if saved or country else {}
    )


@pytest.mark.parametrize("chosen", [0, 9, 1_001])
def test_a_count_out_of_range_is_refused(client, made, chosen):
    response = client.post(
        URL, params={"buyer_id": "ann"}, json={"candidates": chosen}, headers=AUTH
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Choose from 10 to 1,000 candidates."
    assert made == []


@pytest.mark.parametrize(
    ("candidates", "currency", "subtotal", "credits"),
    [(10, "USD", "5000", 5_000), (50, "GBP", "15000", 25_000), (1_000, "EUR", "200000", 500_000)],
)
def test_a_paid_custom_top_up_grants_its_candidates_in_any_currency(
    granted,  # noqa: F811
    candidates,
    currency,
    subtotal,
    credits,
):
    event = completed(candidates=candidates, currency=currency, subtotal=subtotal)

    asyncio.run(webhooks.handle(event))

    assert granted == [("txn_01", "candidates", 1, credits, "acme", "ann")]


def test_a_refund_takes_back_its_share_of_the_candidates_credits():
    # 50 candidates for $200: $100 back takes back half.
    assert adjustments.share(25_000, "10000", "20000") == 12_500


def test_the_refusal_names_the_range_sold():
    low = min(candidate_tiers(currency)[0][0] for currency in Currency)

    assert CANDIDATES_OUT_OF_RANGE == f"Choose from {low:,} to {CUSTOM_TOP_UP_MAX:,} candidates."
