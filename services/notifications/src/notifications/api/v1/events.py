from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.google import Invoker
from prepza_common.config.constants import RATE_LIMITED, RETRY_AFTER
from prepza_common.events.pubsub import PushBody, event_of

from notifications.handlers.dispatch import handle
from notifications.integrations.resend import ResendBusy

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes every event here. A failed email or Slack post answers with an error, so
    Pub/Sub retries it, and moves it to the dead-letter topic after the subscription's maximum
    attempts; neither Resend nor Slack gets the same message twice. Over Resend's per-second limit
    (a burst of invites) it answers 429: Pub/Sub retries with backoff, and it isn't counted as a
    server error."""
    event_type, data, event_id = event_of(body)

    try:
        await handle(event_type, data, event_id)
    except ResendBusy:
        # Resend's limit is per second.
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, RATE_LIMITED, headers={RETRY_AFTER: "1"}
        ) from None
