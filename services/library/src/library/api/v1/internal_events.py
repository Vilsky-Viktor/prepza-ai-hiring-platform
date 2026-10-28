from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events.pubsub import PushBody, event_of

from library.handlers.dispatch import handle

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes every event here. A failure answers with an error, so Pub/Sub retries it,
    and moves it to the dead-letter topic after the subscription's maximum attempts."""
    # The event's id stays the same however often it's delivered or re-sent (event_of).
    event_type, data, event_id = event_of(body)
    await handle(event_id, event_type, data)
