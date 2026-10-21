import asyncio
import logging
from datetime import UTC, datetime

from prepza_common.analytics import track
from prepza_common.notifications import NotificationKind, notification, publish_quietly

from app.config.settings import settings
from app.constants.notifications import TOP_UP_LINK
from app.constants.products import PADDLE_API_ORIGIN, OwnerType
from app.services import auto_top_ups, credit_events
from app.services import outbox as outbox_service
from app.services.catalog import bought
from app.services.referrals import reward_after_top_up
from app.storage import ledger, purchases

logger = logging.getLogger(__name__)


async def handle_completed(data: dict) -> None:
    """Adds the credits a completed top-up bought. Whose wallet they go to comes from the
    checkout billing created, or for an automatic top-up from its subscription; the candidates come
    from the price billing made, the same whatever the currency paid in."""
    custom = data.get("custom_data") or {}
    owner_id = custom.get("owner_id")
    owner_type = custom.get("owner_type")
    subscription_id = data.get("subscription_id")

    if subscription_id:
        # The checkout that turns automatic top-up on; its $0 price buys nothing.
        await auto_top_ups.start(custom, subscription_id, data["currency_code"])
        owner_type, owner_id = await auto_top_ups.owner(subscription_id) or (
            owner_type,
            owner_id,
        )

    if not owner_id or owner_type not in tuple(OwnerType):
        logger.warning("Transaction %s has no valid owner", data["id"])

        return

    # A top-up's checkout is made by the backend, which checked the buyer may pay into the
    # wallet; one opened in the browser could name anyone.
    if not subscription_id and data.get("origin") != PADDLE_API_ORIGIN:
        logger.error("Transaction %s wasn't created by billing: refund it", data["id"])

        return

    # The company was deleted between the checkout and the payment.
    if owner_id not in await ledger.wallets(owner_type, [owner_id]):
        logger.error("Transaction %s pays into a wallet that's gone: refund it", data["id"])

        return

    for index, item in enumerate(data.get("items", [])):
        if item["price"]["id"] == settings.paddle_price_auto_top_up:
            continue

        quantity = item.get("quantity", 1)
        found = bought(index, item, data)

        if found is None:
            logger.error(
                "Item %s of transaction %s isn't one we sell: refund it",
                item["price"]["id"],
                data["id"],
            )

            continue

        key, paid_cents, credits = found
        granted = await purchases.grant(
            owner_type,
            owner_id,
            credits,
            quantity,
            data["id"],
            key,
            custom.get("buyer_id"),
            data["details"]["totals"]["grand_total"],
            data["currency_code"],
            datetime.now(UTC),
            subscription_id is not None,
        )

        # Paid once (it's idempotent), also on Paddle's retry after a failure right after the
        # grant, so the referral is never lost.
        await reward_after_top_up(owner_type, owner_id, data["id"])

        if granted:
            await announce_top_up(
                owner_type, owner_id, paid_cents, key, credits, data, subscription_id
            )


async def announce_top_up(
    owner_type, owner_id, paid_cents, key, credits, data, subscription_id
) -> None:
    """Tells everyone of a new top-up: the action log, the services waiting for credits, the
    funnel and, for an automatic one, the owner's bell. All at once, never one after another:
    each waits at most PUBLISH_IN_REQUEST_TIMEOUT_SECONDS and none raises, so Paddle gets its
    answer within its 5 seconds even when Pub/Sub is slow, instead of retrying."""
    steps = [
        outbox_service.flush_quietly(),
        credit_events.credits_added(owner_type, owner_id),
        track(
            "topped_up",
            company_id=owner_id,
            amount_cents=paid_cents,
            product=key,
            currency=data["currency_code"],
            automatic=subscription_id is not None,
        ),
    ]

    if subscription_id:
        steps.append(
            publish_quietly(
                notification(
                    owner_type,
                    owner_id,
                    NotificationKind.AUTO_TOP_UP_CHARGED,
                    TOP_UP_LINK,
                    credits=credits,
                )
            )
        )

    await asyncio.gather(*steps)
