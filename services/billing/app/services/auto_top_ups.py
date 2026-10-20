import asyncio
import logging
from datetime import UTC, datetime

import httpx
from fastapi import HTTPException, status
from prepza_common.analytics import track
from prepza_common.notifications import NotificationKind, notification, publish_quietly

from app.config.settings import settings
from app.constants.notifications import TOP_UP_LINK
from app.constants.products import (
    AUTO_TOP_UP_FLAG,
    AUTO_TOP_UP_THRESHOLDS,
    AUTO_TOP_UP_WAIT_SECONDS,
    NOT_YOUR_AUTO_TOP_UP,
    SUBSCRIPTION_ENDED_STATUS,
    TOP_UP_UNAVAILABLE,
)
from app.integrations import paddle
from app.schemas.billing import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from app.services.catalog import price_ids
from app.storage import auto_top_ups

logger = logging.getLogger(__name__)


def offered() -> bool:
    return bool(settings.paddle_api_key and settings.paddle_price_auto_top_up)


def products() -> list[str]:
    """The top-ups it can buy: the fixed ones on sale."""
    return [key for key, price in price_ids().items() if price]


async def out(owner_type: str, owner_id: str) -> AutoTopUpOut:
    row = await auto_top_ups.get(owner_type, owner_id)
    started = row is not None and row.subscription_id is not None

    return AutoTopUpOut(
        offered=offered(),
        on=started,
        waiting=row is not None and not started,
        product=row.product if row else None,
        threshold=row.threshold if row else None,
        products=products(),
        thresholds=AUTO_TOP_UP_THRESHOLDS,
    )


async def turn_on(owner_type: str, owner_id: str, body: AutoTopUpIn, buyer_id: str) -> AutoTopUpOut:
    """Saves the choice. If it isn't running yet, the answer carries the checkout that saves
    the card; it starts when Paddle confirms the subscription."""
    if not offered() or body.product not in products():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, TOP_UP_UNAVAILABLE)

    if body.threshold not in AUTO_TOP_UP_THRESHOLDS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Choose one of the balances")

    current = await auto_top_ups.get(owner_type, owner_id)

    # Running, it charges its buyer's card: another member may turn it off, not change it.
    if current and current.subscription_id and current.buyer_id != buyer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_YOUR_AUTO_TOP_UP)

    row = await auto_top_ups.save(owner_type, owner_id, body.product, body.threshold, buyer_id)
    result = await out(owner_type, owner_id)

    if row.subscription_id is None:
        result.checkout = CheckoutOut(
            price_id=settings.paddle_price_auto_top_up,
            custom_data={
                "owner_type": owner_type,
                "owner_id": owner_id,
                "buyer_id": buyer_id,
                AUTO_TOP_UP_FLAG: "1",
            },
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


async def start(custom: dict, subscription_id: str) -> None:
    """Paddle confirmed the checkout's subscription. One nobody is waiting for (turned off
    meanwhile, or not started by whoever turned it on) is cancelled, so no card is kept. One
    that already ended (its subscription.canceled came first) isn't started."""
    if custom.get(AUTO_TOP_UP_FLAG) != "1":
        return

    owner = (custom.get("owner_type"), custom.get("owner_id"))

    if await auto_top_ups.owner_of(subscription_id) == owner:
        return

    if await paddle.subscription_status(subscription_id) == SUBSCRIPTION_ENDED_STATUS:
        return

    if not await auto_top_ups.start(*owner, custom.get("buyer_id"), subscription_id):
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


async def check_briefly(owner_type: str, owner_id: str) -> None:
    """check(), waited for at most AUTO_TOP_UP_WAIT_SECONDS, so the request that used the credits
    isn't held long and nothing runs after its answer. Cut off, the charge counts as one whose
    answer was lost: its web hook adds the credits if Paddle took it."""
    try:
        await asyncio.wait_for(check(owner_type, owner_id), AUTO_TOP_UP_WAIT_SECONDS)
    except TimeoutError:
        logger.warning("Automatic top-up cut off for %s %s", owner_type, owner_id)


async def check(owner_type: str, owner_id: str) -> None:
    """After credits are used: if the balance is now under the threshold, buys the chosen
    top-up with the saved card. Never fails the request that used the credits; a charge Paddle
    refuses (a declined card) is told to the owner and tried again only after
    AUTO_TOP_UP_RETRY_AFTER. After a timeout or Paddle's own error the charge may have gone
    through: its transaction.completed web hook adds the credits. Until a charge's credits come,
    none follows it, for at most AUTO_TOP_UP_UNCREDITED_WAIT (claim_charge)."""
    row = None
    now = datetime.now(UTC)

    try:
        row = await auto_top_ups.claim_charge(owner_type, owner_id, now)

        if row is None:
            return

        await paddle.charge(row.subscription_id, price_ids()[row.product])
    except Exception as error:
        logger.exception("Automatic top-up failed for %s %s", owner_type, owner_id)

        if isinstance(error, httpx.HTTPStatusError) and error.response.is_client_error:
            await auto_top_ups.failed(owner_type, owner_id, now)
            await publish_quietly(
                notification(owner_type, owner_id, NotificationKind.AUTO_TOP_UP_FAILED, TOP_UP_LINK)
            )
