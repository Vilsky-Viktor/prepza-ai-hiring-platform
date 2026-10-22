import asyncio
import logging
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from prepza_common.analytics import track
from prepza_common.constants import DEFAULT_LANGUAGE

from app.config.settings import settings
from app.constants.currencies import DEFAULT_CURRENCY, Currency
from app.constants.products import (
    AUTO_TOP_UP_FLAG,
    AUTO_TOP_UP_THRESHOLDS,
    AUTO_TOP_UP_WAIT_SECONDS,
    NOT_YOUR_AUTO_TOP_UP,
    SUBSCRIPTION_ENDED_STATUS,
    TOP_UP_UNAVAILABLE,
    TOP_UPS,
)
from app.helpers.credits import top_up_price
from app.integrations import paddle
from app.models.billing import AutoTopUp
from app.schemas.billing import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from app.services.auto_top_up_declines import declined, handle_decline
from app.services.auto_top_up_prices import charge_price, listed
from app.services.catalog import candidates_price
from app.services.currencies import decide
from app.storage import auto_top_up_charges, auto_top_ups

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
    row = await auto_top_ups.get(owner_type, owner_id)
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

    current = await auto_top_ups.get(owner_type, owner_id)

    # Running, it charges its buyer's card: another member may turn it off, not change it.
    if current and current.subscription_id and current.buyer_id != buyer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_YOUR_AUTO_TOP_UP)

    row = await auto_top_ups.save(
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
    row = await auto_top_ups.get(owner_type, owner_id)

    if row is None or (buyer_id is not None and row.buyer_id != buyer_id):
        return

    if row.subscription_id:
        await cancel(row.subscription_id)

    left = await auto_top_ups.remove(owner_type, owner_id, buyer_id)

    # One started meanwhile goes too.
    if left and left != row.subscription_id:
        await cancel(left)


async def forget_buyer(buyer_id: str) -> None:
    """A deleted account's card is never charged again: its automatic top-ups' subscriptions
    are cancelled, then they go off. If Paddle can't cancel one, this raises and the account's
    deletion is tried again."""
    rows = await auto_top_ups.of_buyer(buyer_id)
    cancelled = {row.subscription_id for row in rows if row.subscription_id}

    for subscription_id in cancelled:
        await cancel(subscription_id)

    for subscription_id in set(await auto_top_ups.remove_for_buyer(buyer_id)) - cancelled:
        await cancel(subscription_id)


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

    if await auto_top_ups.owner_of(subscription_id) == owner:
        return

    if await paddle.subscription_status(subscription_id) == SUBSCRIPTION_ENDED_STATUS:
        return

    if not await auto_top_ups.start(*owner, custom.get("buyer_id"), subscription_id, currency):
        await cancel_quietly(subscription_id)

        return

    await track("auto_top_up_on", company_id=owner[1])
    # The balance may already be under the threshold.
    await check(*owner)


async def owner(subscription_id: str) -> tuple[str, str] | None:
    """Whose wallet an automatic charge on this subscription is for."""
    return await auto_top_ups.owner_of(subscription_id)


async def ended(subscription_id: str) -> None:
    """Paddle ended the subscription (cancelled there, or after failed payments): it's off."""
    await auto_top_ups.remove_subscription(subscription_id)


async def card_saved(subscription_id: str, saved_at: datetime) -> None:
    """Paddle saved a new card for the subscription at `saved_at`: a pause from before then ends,
    and a balance already under the threshold is topped up with the new card at once."""
    owner = await auto_top_up_charges.resume(subscription_id, saved_at)

    if owner:
        await check_briefly(*owner)


async def check_briefly(owner_type: str, owner_id: str) -> None:
    """check(), waited for at most AUTO_TOP_UP_WAIT_SECONDS, so the request that used the credits
    isn't held long and nothing runs after its answer. Cut off, the charge counts as one whose
    answer was lost: its web hook adds the credits if Paddle took it."""
    try:
        await asyncio.wait_for(check(owner_type, owner_id), AUTO_TOP_UP_WAIT_SECONDS)
    except TimeoutError:
        logger.warning("Automatic top-up cut off for %s %s", owner_type, owner_id)


def top_up_item(product_key: str, price: int, currency: Currency, language: str) -> dict:
    """The fixed top-up the automatic top-up buys, at `price` (minor units) in `currency`, named
    in `language`."""
    product = next(product for product in TOP_UPS if product.key == product_key)

    return candidates_price(
        product.candidates, price // product.candidates, currency, product.key, language
    )


async def charge(row: AutoTopUp, owner_id: str, now: datetime) -> tuple[int, Currency]:
    """Charges the chosen top-up in the company's currency now, at its agreed price
    (charge_price); what it charged. Paddle charges a subscription in its own currency
    (converting a price in another), so one set up in another currency is switched to the
    company's first, nothing billed for the switch."""
    currency = await decide(None, company_id=owner_id)
    price = charge_price(row, currency, now)

    if (row.currency or DEFAULT_CURRENCY) != currency:
        await paddle.set_currency(row.subscription_id, currency)
        await auto_top_ups.set_currency(row.subscription_id, currency)

    # Named in the language of whoever turned it on; set up before languages were kept, English.
    item = top_up_item(row.product, price, currency, row.language or DEFAULT_LANGUAGE)
    await paddle.charge(row.subscription_id, item)

    return price, currency


async def check(owner_type: str, owner_id: str) -> None:
    """After credits are used: if the balance is now under the threshold, buys the chosen
    top-up with the saved card. Never fails the request that used the credits. A charge Paddle
    refuses (a declined card) is told to the company and tried again later, a few times at
    most (AUTO_TOP_UP_RETRY_WAITS), or never, once the decline can't pass later: then it pauses
    until the card is updated (auto_top_up_declines). After a timeout or Paddle's own error the
    charge may have gone through: its transaction.completed web hook adds the credits. Until a
    charge's credits come, none follows it, for at most AUTO_TOP_UP_UNCREDITED_WAIT
    (claim_charge)."""
    row = None
    now = datetime.now(UTC)

    try:
        row = await auto_top_ups.claim_charge(owner_type, owner_id, now)

        if row is None:
            return

        price, currency = await charge(row, owner_id, now)
    except Exception as error:
        logger.exception("Automatic top-up failed for %s %s", owner_type, owner_id)

        if row is not None and declined(error):
            await handle_decline(row, owner_type, owner_id, now)

        return

    await auto_top_up_charges.charged(owner_type, owner_id, price, currency, now)
