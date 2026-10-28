import logging
import time

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.config.constants import WEBHOOK_SIGNATURE_REFUSED

from notifications.config import settings
from notifications.constants.webhooks import WEBHOOK_FIELDS, WEBHOOK_TOLERANCE_SECONDS
from notifications.helpers.webhooks import signature_valid
from notifications.repositories import webhook_deliveries
from notifications.services import outbox as outbox_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/resend", status_code=status.HTTP_204_NO_CONTENT)
async def resend_webhook(request: Request) -> None:
    """Answered once the signature is checked and the event recorded (by its delivery id, so a
    repeat is recorded once): its work runs from the email.webhook_received event
    (services/webhooks.py), retried by Pub/Sub, not before the answer."""
    body = await request.body()

    if not signature_valid(
        request.headers.get("svix-id", ""),
        request.headers.get("svix-timestamp", ""),
        request.headers.get("svix-signature", ""),
        body,
        settings.resend_webhook_secret,
        time.time(),
        WEBHOOK_TOLERANCE_SECONDS,
    ):
        logger.error("%s: resend", WEBHOOK_SIGNATURE_REFUSED)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    event = await request.json()
    data = event.get("data") or {}
    kept = {
        "type": event.get("type"),
        "data": {key: data[key] for key in WEBHOOK_FIELDS if key in data},
    }
    await webhook_deliveries.record(request.headers["svix-id"], kept)
    await outbox_service.flush_quietly()
