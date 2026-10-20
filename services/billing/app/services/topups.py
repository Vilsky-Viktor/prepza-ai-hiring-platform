import logging
from datetime import UTC, datetime

from prepza_common.analytics import track
from prepza_common.notifications import NotificationKind, notification, publish_quietly

from app.config.settings import settings
from app.constants.notifications import TOP_UP_LINK
from app.constants.products import PADDLE_API_ORIGIN, OwnerType
from app.services import auto_top_ups, credit_events
from app.services import outbox as outbox_service
from app.services.catalog import bought_for, custom_bought
from app.services.referrals import reward_after_top_up
from app.storage import ledger, purchases

logger = logging.getLogger(__name__)


async def handle_completed(data: dict) -> None:
    """Adds the credits a completed top-up bought. Whose wallet they go to comes from the
    checkout billing created, or for an automatic top-up from its subscription; the amount comes
    from Paddle's price id."""
    custom = data.get("custom_data") or {}
    owner_id = custom.get("owner_id")
    owner_type = custom.get("owner_type")
    subscription_id = data.get("subscription_id")

    if subscription_id:
        # The checkout that turns automatic top-up on; its $0 price buys nothing.
        await auto_top_ups.start(custom, subscription_id)
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

    for item in data.get("items", []):
        if item["price"]["id"] == settings.paddle_price_auto_top_up:
            continue

        quantity = item.get("quantity", 1)
        found = bought_for(item["price"]["id"], quantity) or custom_bought(item, custom)

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
            await outbox_service.flush_quietly()
            await credit_events.credits_added(owner_type, owner_id)
            await track(
                "topped_up",
                company_id=owner_id,
                amount_cents=paid_cents,
                product=key,
                currency=data["currency_code"],
                automatic=subscription_id is not None,
            )

            if subscription_id:
                await publish_quietly(
                    notification(
                        owner_type,
                        owner_id,
                        NotificationKind.AUTO_TOP_UP_CHARGED,
                        TOP_UP_LINK,
                        credits=credits,
                    )
                )
