from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events.pubsub import PushBody, event_of

from assistant.handlers.dispatch import handle

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes company.deleted here. A failure answers with an error, so Pub/Sub retries
    it, and moves it to the dead-letter topic after the subscription's maximum attempts."""
    event_type, data, _ = event_of(body)
    await handle(event_type, data)
