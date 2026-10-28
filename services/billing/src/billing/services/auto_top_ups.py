import logging
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from prepza_common.config.constants import DEFAULT_LANGUAGE
from prepza_common.events.analytics import track

from billing.config import settings
from billing.constants.currencies import Currency
from billing.constants.products import (
    AUTO_TOP_UP_FLAG,
    AUTO_TOP_UP_THRESHOLDS,
    NOT_YOUR_AUTO_TOP_UP,
    SUBSCRIPTION_ENDED_STATUS,
    TOP_UP_UNAVAILABLE,
    TOP_UPS,
)
from billing.core.db import Session
from billing.helpers.credits import top_up_price
from billing.integrations import paddle
from billing.repositories import auto_top_up_charges, auto_top_ups
from billing.schemas.billing import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from billing.services.auto_top_up_charging import check, check_briefly
from billing.services.auto_top_up_prices import charge_price, listed

logger = logging.getLogger(__name__)


def offered() -> bool:
    return bool(
        settings.paddle_api_key
        and settings.paddle_price_auto_top_up
        and settings.paddle_product_candidates
    )


def products() -> list[str]:
    """The top-ups it can buy: the fixed ones."""
    return [product.key for product in TOP_UPS]


async def out(owner_type: str, owner_id: str, currency: Currency) -> AutoTopUpOut:
    """With each top-up's price in `currency`, the company's, which every charge is in; the
    chosen one at what it charges now (its agreed price), with a new price announced and its
    day."""
    async with Session() as session:
        row = await auto_top_ups.get(session, owner_type, owner_id)

    started = row is not None and row.subscription_id is not None
    sold = products()
    prices = {
        product.key: top_up_price(product, currency) for product in TOP_UPS if product.key in sold
    }
    coming = None

    if row is not None and row.product in prices:
        prices[row.product] = charge_price(row, currency, datetime.now(UTC))
        announced = row.price_currency == currency and row.next_price is not None
        coming = row if announced and prices[row.product] != row.next_price else None

    return AutoTopUpOut(
        offered=offered(),
        on=started,
        waiting=row is not None and not started,
        paused=started and row.paused_at is not None,
        product=row.product if row else None,
        threshold=row.threshold if row else None,
        products=sold,
        thresholds=AUTO_TOP_UP_THRESHOLDS,
        currency=currency,
        prices=prices,
        next_price=coming.next_price if coming else None,
        next_price_from=coming.next_price_from if coming else None,
    )


async def turn_on(
    owner_type: str,
    owner_id: str,
    body: AutoTopUpIn,
    buyer_id: str,
    currency: Currency,
    language: str = DEFAULT_LANGUAGE,
) -> AutoTopUpOut:
    """Saves the choice, and the buyer's `language`, which names what each charge buys. If it
    isn't running yet, the answer carries the checkout that saves the card; it starts when
    Paddle confirms the subscription."""
    if not offered() or body.product not in products():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, TOP_UP_UNAVAILABLE)

    if body.threshold not in AUTO_TOP_UP_THRESHOLDS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Choose one of the balances")

    async with Session.begin() as session:
        current = await auto_top_ups.get(session, owner_type, owner_id)

        # Running, it charges its buyer's card: another member may turn it off, not change it.
        if current and current.subscription_id and current.buyer_id != buyer_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_YOUR_AUTO_TOP_UP)

        row = await auto_top_ups.save(
            session,
            owner_type,
            owner_id,
            body.product,
            body.threshold,
            buyer_id,
            listed(body.product, currency),
            currency,
            language,
        )

    result = await out(owner_type, owner_id, currency)

    # The $0 subscription that saves the card, in the company's currency, which every top-up
    # it charges keeps.
    if row.subscription_id is None:
        custom = {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "buyer_id": buyer_id,
            AUTO_TOP_UP_FLAG: "1",
        }
        item = {"price_id": settings.paddle_price_auto_top_up, "quantity": 1}
        result.checkout = CheckoutOut(
            transaction_id=await paddle.create_transaction([item], currency, custom)
        )

    return result


async def turn_off(owner_type: str, owner_id: str, buyer_id: str | None = None) -> None:
    """Off, once the subscription that keeps the card is cancelled: if Paddle can't cancel it,
    nothing changes and this raises, so turning it off (or deleting the company) can be tried
    again. With `buyer_id`, only if that person's card pays for it (a member removed)."""
    async with Session() as session:
        row = await auto_top_ups.get(session, owner_type, owner_id)

    if row is None or (buyer_id is not None and row.buyer_id != buyer_id):
        return

    if row.subscription_id:
        await cancel(row.subscription_id)

    async with Session.begin() as session:
        left = await auto_top_ups.remove(session, owner_type, owner_id, buyer_id)

    # One started meanwhile goes too.
    if left and left != row.subscription_id:
        await cancel(left)


async def cancel_for_buyer(buyer_id: str) -> set[str]:
    """Cancels the subscriptions of the automatic top-ups paid with this person's card, so it's
    never charged again; the ones cancelled. If Paddle can't cancel one, this raises and the
    account's deletion is tried again (services/accounts.py)."""
    async with Session() as session:
        rows = await auto_top_ups.of_buyer(session, buyer_id)

    cancelled = {row.subscription_id for row in rows if row.subscription_id}

    for subscription_id in cancelled:
        await cancel(subscription_id)

    return cancelled


async def cancel(subscription_id: str) -> None:
    """Cancels the subscription; one Paddle has already ended counts as cancelled. Raises
    otherwise."""
    try:
        await paddle.cancel(subscription_id)
    except httpx.HTTPStatusError:
        if await paddle.subscription_status(subscription_id) != SUBSCRIPTION_ENDED_STATUS:
            raise


async def cancel_quietly(subscription_id: str) -> None:
    try:
        await paddle.cancel(subscription_id)
    except Exception:
        logger.exception("Couldn't cancel subscription %s", subscription_id)


async def start(custom: dict, subscription_id: str, currency: str) -> None:
    """Paddle confirmed the checkout's subscription, in `currency`. One nobody is waiting for (turned off
    meanwhile, or not started by whoever turned it on) is cancelled, so no card is kept. One
    that already ended (its subscription.canceled came first) isn't started."""
    if custom.get(AUTO_TOP_UP_FLAG) != "1":
        return

    owner = (custom.get("owner_type"), custom.get("owner_id"))

    if await owner_of(subscription_id) == owner:
        return

    if await paddle.subscription_status(subscription_id) == SUBSCRIPTION_ENDED_STATUS:
        return

    async with Session.begin() as session:
        started = await auto_top_ups.start(
            session, *owner, custom.get("buyer_id"), subscription_id, currency
        )

    if not started:
        await cancel_quietly(subscription_id)

        return

    await track("auto_top_up_on", company_id=owner[1])
    # The balance may already be under the threshold.
    await check(*owner)


async def owner_of(subscription_id: str) -> tuple[str, str] | None:
    """Whose wallet an automatic charge on this subscription is for."""
    async with Session() as session:
        return await auto_top_ups.owner_of(session, subscription_id)


async def ended(subscription_id: str) -> None:
    """Paddle ended the subscription (cancelled there, or after failed payments): it's off."""
    async with Session.begin() as session:
        await auto_top_ups.remove_subscription(session, subscription_id)


async def card_saved(subscription_id: str, saved_at: datetime) -> None:
    """Paddle saved a new card for the subscription at `saved_at`: a pause from before then ends,
    and a balance already under the threshold is topped up with the new card at once."""
    async with Session.begin() as session:
        owner = await auto_top_up_charges.resume(session, subscription_id, saved_at)

    if owner:
        await check_briefly(*owner)
