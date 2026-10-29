"""A top-up's item, which Paddle shows at checkout and on the invoice, is named in the buyer's
language: the number as that language writes it, the noun in its plural form for it."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.config.constants import LANGUAGES

from billing.constants.item_names import CANDIDATES_NAMES
from billing.helpers.item_names import candidates_name
from billing.integrations import paddle
from billing.services import auto_top_up_charging
from tests.unit.services.test_custom_top_ups import URL, made, product  # noqa: F401 (fixtures)


@pytest.mark.parametrize(
    ("language", "count", "name"),
    [
        ("en", 1_000, "1,000 candidates"),
        ("en", 1, "1 candidate"),
        ("de", 1_000, "1.000 Kandidaten"),
        # Russian: one, few and many, by the number's last digits.
        ("ru", 21, "21 кандидат"),
        ("ru", 50, "50 кандидатов"),
        ("ru", 22, "22 кандидата"),
        ("ru", 1_000, "1\xa0000 кандидатов"),
        ("fr", 1_000, "1 000 candidats"),
        # Arabic: two, few, many and other forms.
        ("ar", 2, "مرشحان"),
        ("ar", 10, "10 مرشحين"),
        ("ar", 50, "50 مرشحًا"),
        ("ar", 1_000, "1,000 مرشح"),
        # Japanese has no plural: one form, with the counter word.
        ("ja", 1_000, "候補者 1,000 人"),
        ("ja", 1, "候補者 1 人"),
        ("fa", 200, "200 متقاضی"),
        # A language the site doesn't have: English.
        ("xx", 10, "10 candidates"),
    ],
)
def test_the_name_is_written_as_the_buyers_language_writes_it(language, count, name):
    assert candidates_name(count, language) == name


def test_every_site_language_has_its_name():
    assert set(CANDIDATES_NAMES) == set(LANGUAGES)
    assert all("other" in forms for forms in CANDIDATES_NAMES.values())


def test_a_checkout_names_its_item_in_the_buyers_language(client, made):  # noqa: F811
    response = client.post(URL, json={"candidates": 1_000}, headers={"Accept-Language": "de"})

    [([item], _, _)] = made
    assert response.status_code == 200
    assert (item["price"]["name"], item["price"]["description"]) == ("1.000 Kandidaten",) * 2
    # What it buys is in its custom data, which the web hooks read, never the name.
    assert item["price"]["custom_data"] == {"candidates": "1000"}


def test_a_checkout_in_a_language_the_site_doesnt_have_is_named_in_english(client, made):  # noqa: F811
    response = client.post(URL, json={"candidates": 10}, headers={"Accept-Language": "xx"})

    [([item], _, _)] = made
    assert response.status_code == 200
    assert item["price"]["name"] == "10 candidates"


@pytest.mark.parametrize(("language", "name"), [("ru", "50 кандидатов"), (None, "50 candidates")])
def test_an_automatic_charge_is_named_in_the_language_of_whoever_turned_it_on(
    monkeypatch, language, name
):
    """One set up before the language was kept is named in English."""
    row = SimpleNamespace(
        subscription_id="sub_1",
        # 50 candidates.
        product="topup_200",
        currency="USD",
        price=None,
        price_currency=None,
        language=language,
    )
    charged = []

    async def charge(subscription_id, price):
        charged.append((price["name"], price["custom_data"]))

    monkeypatch.setattr(paddle, "charge", charge)

    asyncio.run(auto_top_up_charging.charge(row, "acme", datetime.now(UTC)))

    assert charged == [(name, {"top_up": "topup_200"})]
