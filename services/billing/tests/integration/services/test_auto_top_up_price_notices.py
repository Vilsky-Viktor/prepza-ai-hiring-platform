"""An automatic top-up's price against Postgres: agreed when it's set up, kept when only the level
changes, announced once with its notice in the outbox, and charged until its new day comes."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from billing.constants.currencies import Currency
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.models.outbox import OutboxEvent
from billing.repositories import auto_top_up_charges as charges
from billing.repositories import auto_top_up_prices as price_rows
from billing.repositories import auto_top_ups as rows
from billing.schemas.billing import AutoTopUpIn
from billing.services import auto_top_up_prices, auto_top_ups
from tests.integration.services.test_auto_top_ups import checkout_data

COMPANY = OwnerType.COMPANY
DAY = timedelta(days=1)


async def notices(acme: str) -> int:
    """The price notices for acme waiting in billing's outbox."""
    async with Session() as session:
        return await session.scalar(
            select(func.count())
            .select_from(OutboxEvent)
            .where(
                OutboxEvent.data["recipient_id"].astext == acme,
                OutboxEvent.data["kind"].astext == "auto_top_up_price_change",
            )
        )


async def agreed_at(acme: str, ann: str, price: int) -> None:
    """Acme's automatic top-up runs, agreed at `price` (an older price list's)."""
    choice = AutoTopUpIn(product="topup_50", threshold=500)
    await auto_top_ups.turn_on(COMPANY, acme, choice, ann, Currency.USD)
    await auto_top_ups.start(checkout_data(acme, ann), f"sub_{uuid.uuid4().hex[:12]}", "USD")
    await price_rows.agree(COMPANY, acme, price, "USD")


def test_a_new_price_is_announced_once_and_charged_only_from_its_day(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    now = datetime.now(UTC)

    async def scenario():
        await agreed_at(acme, ann, 4500)
        row = await rows.get(COMPANY, acme)
        await auto_top_up_prices.check_price(row, Currency.USD, now)
        # The daily check again, and again with the row read before: one notice.
        await auto_top_up_prices.check_price(await rows.get(COMPANY, acme), Currency.USD, now)
        await auto_top_up_prices.check_price(row, Currency.USD, now)
        announced = await rows.get(COMPANY, acme)
        # Changing only the level keeps both prices.
        level = AutoTopUpIn(product="topup_50", threshold=1500)
        await auto_top_ups.turn_on(COMPANY, acme, level, ann, Currency.USD)
        kept = await rows.get(COMPANY, acme)

        return announced, kept, await notices(acme)

    announced, kept, count = run(scenario())

    assert count == 1
    assert announced.next_price == 5000
    assert announced.next_price_from - now >= timedelta(days=30)
    assert auto_top_up_prices.charge_price(announced, Currency.USD, now) == 4500
    assert auto_top_up_prices.charge_price(announced, Currency.USD, now + 31 * DAY) == 5000
    assert (kept.price, kept.next_price) == (4500, 5000)


def test_charging_on_the_new_day_makes_it_the_agreed_price(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    day = datetime.now(UTC) + 31 * DAY

    async def scenario():
        await agreed_at(acme, ann, 4500)
        row = await rows.get(COMPANY, acme)
        await price_rows.announce(COMPANY, acme, row, 5000, day, {"kind": "test"})
        await charges.charged(COMPANY, acme, 5000, "USD", day)

        return await rows.get(COMPANY, acme)

    row = run(scenario())

    assert (row.price, row.price_currency, row.next_price, row.next_price_from) == (
        5000,
        "USD",
        None,
        None,
    )


def test_choosing_another_top_up_agrees_to_its_price_at_once(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"

    async def scenario():
        await agreed_at(acme, ann, 4500)
        row = await rows.get(COMPANY, acme)
        await price_rows.announce(COMPANY, acme, row, 5000, datetime.now(UTC) + 31 * DAY, {})
        bigger = AutoTopUpIn(product="topup_200", threshold=500)
        await auto_top_ups.turn_on(COMPANY, acme, bigger, ann, Currency.EUR)

        return await rows.get(COMPANY, acme)

    row = run(scenario())

    assert (row.price, row.price_currency, row.next_price) == (20_000, "EUR", None)
