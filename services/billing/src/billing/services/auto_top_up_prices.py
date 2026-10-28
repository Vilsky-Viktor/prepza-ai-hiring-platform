from datetime import UTC, datetime, time, timedelta

from prepza_common.events.notifications import NotificationKind, notification

from billing.constants.auto_top_up_prices import (
    AUTO_TOP_UP_PRICE_NOTICE_DAYS,
    PRICE_CHECK_BATCH,
    PRICE_CHECK_MAX_PAGES,
)
from billing.constants.currencies import DEFAULT_CURRENCY, ChoiceOwner, Currency
from billing.constants.notifications import COMPANY_BILLING_LINK
from billing.constants.products import TOP_UPS
from billing.core.db import Session
from billing.helpers.credits import top_up_price
from billing.models.billing import AutoTopUp
from billing.repositories import auto_top_up_prices, currencies
from billing.services import outbox as outbox_service


def listed(product_key: str, currency: Currency) -> int:
    """What the top-up costs on today's price list, in `currency` (minor units)."""
    product = next(product for product in TOP_UPS if product.key == product_key)

    return top_up_price(product, currency)


def charge_price(row: AutoTopUp, currency: Currency, now: datetime) -> int:
    """What a charge costs now in `currency`, the company's: the price agreed, or the new one
    announced once its day has come. A company that chose another currency since chose its price
    too, and one set up before prices were kept pays today's: both are the price list's."""
    if row.price is None or row.price_currency != currency:
        return listed(row.product, currency)

    if row.next_price is not None and row.next_price_from <= now:
        return row.next_price

    return row.price


async def check_prices(now: datetime) -> None:
    """Daily: each running automatic top-up whose price list now differs from what it charges
    gets the new price from a day at least 30 days ahead, and the company's owners and admins
    are told (a bell notification and an email), once per new price. Charges until then keep the
    agreed price (charge_price). Batched; what's left waits for the next run."""
    after = ("", "")

    for _ in range(PRICE_CHECK_MAX_PAGES):
        async with Session() as session:
            rows = await auto_top_up_prices.running(session, after, PRICE_CHECK_BATCH)
            owners = [row.owner_id for row in rows]
            chosen = await currencies.chosen_many(session, ChoiceOwner.COMPANY, owners)

        for row in rows:
            currency = Currency(chosen.get(row.owner_id, DEFAULT_CURRENCY))
            await check_price(row, currency, now)

        if len(rows) < PRICE_CHECK_BATCH:
            break

        after = (rows[-1].owner_type, rows[-1].owner_id)

    await outbox_service.flush_quietly()


async def check_price(row: AutoTopUp, currency: Currency, now: datetime) -> None:
    price = listed(row.product, currency)

    # Nothing agreed to keep: the price list's from now on, without a notice.
    if row.price is None or row.price_currency != currency or row.price == price:
        if (row.price, row.price_currency, row.next_price) != (price, currency, None):
            async with Session.begin() as session:
                await auto_top_up_prices.agree(
                    session, row.owner_type, row.owner_id, price, currency
                )

        return

    if row.next_price == price:
        return

    since = datetime.combine(
        (now + timedelta(days=AUTO_TOP_UP_PRICE_NOTICE_DAYS)).date(), time(), UTC
    )
    event = notification(
        row.owner_type,
        row.owner_id,
        NotificationKind.AUTO_TOP_UP_PRICE_CHANGE,
        COMPANY_BILLING_LINK.format(owner_id=row.owner_id),
        key=f"{row.owner_id}:{currency}:{price}:{since.date()}",
        price=row.price,
        new_price=price,
        currency=currency,
        date=since.date().isoformat(),
    )
    async with Session.begin() as session:
        await auto_top_up_prices.announce(
            session, row.owner_type, row.owner_id, row, price, since, event
        )
