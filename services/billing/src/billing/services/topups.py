import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from prepza_common.events.analytics import track
from prepza_common.events.notifications import NOTIFICATION_REQUESTED

from billing.config import settings
from billing.constants.declines import PAYMENT_METHOD_CHANGE_ORIGIN
from billing.constants.products import PADDLE_API_ORIGIN, OwnerType
from billing.core.db import Session
from billing.repositories import ledger, purchases
from billing.services import auto_top_ups, credit_events
from billing.services import outbox as outbox_service
from billing.services.auto_top_up_notices import charged
from billing.services.catalog import bought
from billing.services.referrals import reward_after_top_up

logger = logging.getLogger(__name__)


async def handle_completed(data: dict) -> None:
    """Adds the credits a completed top-up bought. Whose wallet they go to comes from the
    checkout billing created, or for an automatic top-up from its subscription; the candidates come
    from the price billing made, the same whatever the currency paid in."""
    custom = data.get("custom_data") or {}
    owner_id = custom.get("owner_id")
    owner_type = custom.get("owner_type")
    subscription_id = data.get("subscription_id")

    # The checkout that saved a new card for automatic top-up: it buys nothing.
    if subscription_id and data.get("origin") == PAYMENT_METHOD_CHANGE_ORIGIN:
        await auto_top_ups.card_saved(subscription_id, datetime.fromisoformat(data["created_at"]))

        return

    if subscription_id:
        # The checkout that turns automatic top-up on; its $0 price buys nothing.
        await auto_top_ups.start(custom, subscription_id, data["currency_code"])
        owner_type, owner_id = await auto_top_ups.owner_of(subscription_id) or (
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

    async with Session() as session:
        existing = await ledger.wallets(session, owner_type, [owner_id])

    # The company was deleted between the checkout and the payment.
    if owner_id not in existing:
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
        # With the credits: the services waiting for them hear of it, and for an automatic
        # top-up the owners' and admins' bell and email, with the credits available after it.
        notice = (
            charged(
                owner_type,
                owner_id,
                data["id"],
                credits,
                data["details"]["totals"]["grand_total"],
                data["currency_code"],
                (data.get("billed_at") or datetime.now(UTC).isoformat())[:10],
            )
            if subscription_id
            else None
        )

        def events_for(available: int, notice=notice) -> list[tuple[str, dict]]:
            events = [credit_events.credits_added(owner_type, owner_id)]

            if notice is not None:
                notice["data"]["available"] = available
                events.append((NOTIFICATION_REQUESTED, notice))

            return events

        granted = await grant(
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
            events_for,
        )

        # Paid once (it's idempotent), also on Paddle's retry after a failure right after the
        # grant, so the referral is never lost.
        await reward_after_top_up(owner_type, owner_id, data["id"])

        if granted:
            await announce_top_up(owner_id, paid_cents, key, data, subscription_id)


async def grant(
    owner_type: str,
    owner_id: str,
    credits: int,
    quantity: int,
    transaction_id: str,
    product: str,
    buyer_id: str | None,
    total: str,
    currency: str,
    now: datetime,
    automatic: bool = False,
    events_for: Callable[[int], list[tuple[str, dict]]] | None = None,
) -> bool:
    """Adds a paid top-up once per product of a transaction (purchases.grant), with its events
    for the outbox (`events_for` the credits available after it), and a member's own top-up to
    the company's action log in the same save; an automatic one isn't theirs."""
    async with Session.begin() as session:
        granted = await purchases.grant(
            session,
            owner_type,
            owner_id,
            credits,
            quantity,
            transaction_id,
            product,
            buyer_id,
            total,
            currency,
            now,
            automatic,
            events_for,
        )

        if granted and owner_type == OwnerType.COMPANY and buyer_id and not automatic:
            purchases.log_top_up(session, owner_id, buyer_id)

    return granted


async def announce_top_up(owner_id, paid_cents, key, data, subscription_id) -> None:
    """Tells everyone of a new top-up: the outbox's events saved with it (the action log, the
    services waiting for credits, an automatic one's bell) and the funnel. At once, never one
    after another: each waits at most PUBLISH_IN_REQUEST_TIMEOUT_SECONDS and none raises, so
    Paddle gets its answer within its 5 seconds even when Pub/Sub is slow, instead of
    retrying; the outbox's next run publishes what this one couldn't."""
    steps = [
        outbox_service.flush_quietly(),
        track(
            "topped_up",
            company_id=owner_id,
            amount_cents=paid_cents,
            product=key,
            currency=data["currency_code"],
            automatic=subscription_id is not None,
        ),
    ]

    await asyncio.gather(*steps)
