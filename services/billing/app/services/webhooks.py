from app.constants.products import (
    ADJUSTMENT_EVENTS,
    SUBSCRIPTION_CANCELED,
    SUBSCRIPTION_CREATED,
    TRANSACTION_COMPLETED,
)
from app.services import auto_top_ups
from app.services.adjustments import handle_adjustment
from app.services.topups import handle_completed


async def handle(event: dict) -> None:
    """Paddle's events: a paid top-up adds credits; refunds and chargebacks take them back;
    an automatic top-up's subscription starts it or, when it ends, turns it off."""
    event_type = event.get("event_type")

    if event_type == TRANSACTION_COMPLETED:
        await handle_completed(event["data"])
    elif event_type in ADJUSTMENT_EVENTS:
        await handle_adjustment(event["data"])
    elif event_type == SUBSCRIPTION_CREATED:
        data = event["data"]
        await auto_top_ups.start(data.get("custom_data") or {}, data["id"], data["currency_code"])
    elif event_type == SUBSCRIPTION_CANCELED:
        await auto_top_ups.ended(event["data"]["id"])
