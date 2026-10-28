"""What an automatic top-up charges: the price agreed until a new one, announced at least 30 days
ahead, has its day; a currency or a top-up the company chose applies at once."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from billing.repositories import auto_top_up_prices as price_rows
from billing.services import auto_top_up_prices
from billing.services.auto_top_up_prices import charge_price, check_price

NOW = datetime(2026, 10, 21, 15, 30, tzinfo=UTC)
# Midnight UTC 31 days after NOW: at least 30 days after the notice.
FROM = datetime(2026, 11, 21, tzinfo=UTC)
LISTED = 5000  # topup_50 in USD and EUR today


def row(price=None, currency=None, next_price=None, next_from=None):
    return SimpleNamespace(
        owner_type="company",
        owner_id="acme",
        product="topup_50",
        price=price,
        price_currency=currency,
        next_price=next_price,
        next_price_from=next_from,
    )


@pytest.mark.parametrize(
    ("top_up", "currency", "charged"),
    [
        # Set up before prices were kept: the price list's.
        (row(), "USD", LISTED),
        # Agreed at $45: still $45, the price list's new price not announced yet.
        (row(4500, "USD"), "USD", 4500),
        # A new price announced for a day still to come: the agreed one until then.
        (row(4500, "USD", 5000, FROM), "USD", 4500),
        # Its day came: the new one.
        (row(4500, "USD", 5000, NOW), "USD", 5000),
        # The company chose euros since: the price list's in euros, at once.
        (row(4500, "USD", 4800, NOW), "EUR", LISTED),
    ],
)
def test_each_charge_costs_the_agreed_price_until_a_new_ones_day(top_up, currency, charged):
    assert charge_price(top_up, currency, NOW) == charged


@pytest.fixture
def recorded(monkeypatch):
    """What the check did: prices agreed at once, and new prices announced (with their notice)."""
    done = {"agreed": [], "announced": []}

    async def agree(owner_type, owner_id, price, currency):
        done["agreed"].append((owner_id, price, currency))

    async def announce(owner_type, owner_id, read, price, since, event):
        done["announced"].append((price, since, event))

        return True

    monkeypatch.setattr(price_rows, "agree", agree)
    monkeypatch.setattr(price_rows, "announce", announce)

    return done


def test_a_new_price_is_announced_from_a_day_at_least_30_days_ahead(recorded):
    asyncio.run(check_price(row(4500, "USD"), "USD", NOW))

    [(price, since, event)] = recorded["announced"]
    assert (price, since) == (LISTED, FROM)
    assert event["kind"] == "auto_top_up_price_change"
    assert event["recipient"] == "company"
    assert event["link"] == "/companies/acme/billing"
    assert event["data"] == {
        "price": 4500,
        "new_price": LISTED,
        "currency": "USD",
        "date": "2026-11-21",
    }
    assert recorded["agreed"] == []


@pytest.mark.parametrize(
    ("top_up", "currency", "agreed"),
    [
        # Already announced: nothing again.
        (row(4500, "USD", LISTED, FROM), "USD", []),
        # Agreed at the price list's: nothing to do.
        (row(LISTED, "USD"), "USD", []),
        # The price list went back to the agreed price: the announced one is dropped.
        (row(LISTED, "USD", 6000, FROM), "USD", [("acme", LISTED, "USD")]),
        # Set up before prices were kept, or the company chose another currency: today's price
        # is agreed without a notice.
        (row(), "USD", [("acme", LISTED, "USD")]),
        (row(4500, "USD"), "EUR", [("acme", LISTED, "EUR")]),
    ],
)
def test_no_notice_when_nothing_agreed_changes(recorded, top_up, currency, agreed):
    asyncio.run(check_price(top_up, currency, NOW))

    assert recorded["announced"] == []
    assert recorded["agreed"] == agreed


def test_the_daily_check_reads_every_running_one_page_by_page(monkeypatch, recorded):
    """Two pages; each company's own currency, US dollars without one."""
    pages = {("", ""): [row(4500, "USD")], ("company", "acme"): []}
    seen = []

    async def running(after, limit):
        seen.append(after)

        return pages[after]

    async def chosen_many(owner_type, owner_ids):
        return {}

    async def flushed():
        seen.append("flushed")

    monkeypatch.setattr(price_rows, "running", running)
    monkeypatch.setattr(auto_top_up_prices, "PRICE_CHECK_BATCH", 1)
    monkeypatch.setattr("billing.repositories.currencies.chosen_many", chosen_many)
    monkeypatch.setattr(auto_top_up_prices.outbox_service, "flush_quietly", flushed)

    asyncio.run(auto_top_up_prices.check_prices(NOW))

    # The notices go out at the end, through the outbox.
    assert seen == [("", ""), ("company", "acme"), "flushed"]
    assert [price for price, _, _ in recorded["announced"]] == [LISTED]
