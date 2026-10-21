import logging
from datetime import datetime

import httpx
from fastapi import HTTPException, status
from prepza_common.notifications import NotificationKind, notification

from app.constants.declines import DECLINE_READ_TIMEOUT_SECONDS, HARD_DECLINE_CODES
from app.constants.notifications import COMPANY_BILLING_LINK, TOP_UP_LINK
from app.constants.products import NOT_YOUR_AUTO_TOP_UP, PADDLE_REFUSES_BILLING
from app.integrations import paddle
from app.models.billing import AutoTopUp
from app.schemas.billing import CheckoutOut
from app.services import outbox as outbox_service
from app.storage import auto_top_up_charges, auto_top_ups
from app.storage.events import tell

logger = logging.getLogger(__name__)

# Turning a paused automatic top-up back on needs one that's running.
NOT_RUNNING = "Automatic top-up isn't on"


def declined(error: Exception) -> bool:
    """Whether Paddle refused the charge itself (a declined card), not billing: its key or rate
    limit failing is billing's problem, never told to the owner as their card's."""
    return (
        isinstance(error, httpx.HTTPStatusError)
        and error.response.is_client_error
        and error.response.status_code not in PADDLE_REFUSES_BILLING
    )


async def hard(subscription_id: str, since: datetime) -> bool:
    """Whether the card's decline is one that can't pass later (HARD_DECLINE_CODES), by the
    failed payment Paddle recorded; not known (Paddle slow, no code) counts as one that may."""
    try:
        code = await paddle.charge_error(subscription_id, since, DECLINE_READ_TIMEOUT_SECONDS)
    except (httpx.HTTPError, KeyError):
        logger.warning("Couldn't read why subscription %s declined", subscription_id)

        return False

    return code in HARD_DECLINE_CODES


async def handle_decline(row: AutoTopUp, owner_type: str, owner_id: str, now: datetime) -> None:
    """Counts the decline first, so it counts even if what follows is cut off; then pauses at
    once for a decline that can't pass later. The company's owners and admins are told: that it
    failed and will be tried again, or that it's paused until the card is updated."""
    paused = await auto_top_up_charges.declined(owner_type, owner_id, now)

    if not paused and await hard(row.subscription_id, now):
        paused = await auto_top_up_charges.pause(owner_type, owner_id, now)

    if paused:
        event = notification(
            owner_type,
            owner_id,
            NotificationKind.AUTO_TOP_UP_PAUSED,
            COMPANY_BILLING_LINK.format(owner_id=owner_id),
            key=f"{owner_id}:{now.isoformat()}",
        )
    else:
        event = notification(owner_type, owner_id, NotificationKind.AUTO_TOP_UP_FAILED, TOP_UP_LINK)

    # Through the outbox, so a Pub/Sub failure doesn't lose it; sent now if Pub/Sub takes it.
    await tell(event)
    await outbox_service.flush_quietly()


async def card_update(owner_type: str, owner_id: str, buyer_id: str) -> CheckoutOut:
    """The checkout that saves a new card for the running automatic top-up; only for the person
    whose card pays for it. Once Paddle has saved it, a pause ends (auto_top_ups.card_saved)."""
    row = await auto_top_ups.get(owner_type, owner_id)

    if row is None or row.subscription_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_RUNNING)

    if row.buyer_id != buyer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_YOUR_AUTO_TOP_UP)

    return CheckoutOut(transaction_id=await paddle.card_update_transaction(row.subscription_id))
