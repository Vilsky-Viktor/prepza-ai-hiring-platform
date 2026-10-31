from fastapi import APIRouter, status
from testee_common.auth.google import Invoker
from testee_common.events.pubsub import PushBody, event_of, occurred_at
from testee_common.events.unhandleable import handle_or_drop

from api.handlers.dispatch import handle

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes every event here. A failure answers with an error, so Pub/Sub retries it
    with backoff, and moves it to the dead-letter topic after the subscription's maximum
    attempts. An event no retry can handle is logged and acknowledged (handle_or_drop)."""
    event_type, data, event_id = event_of(body)
    await handle_or_drop(
        handle(event_type, data, event_id, occurred_at(body)), event_type, event_id
    )
