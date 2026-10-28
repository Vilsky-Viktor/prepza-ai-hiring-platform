from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events.pubsub import PushBody, event_of, occurred_at
from prepza_common.events.unhandleable import handle_or_drop

from billing.handlers.dispatch import handle

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes the services' records of AI calls and limit hits here. A failure answers
    with an error, so Pub/Sub retries it; an event no retry can handle is logged and
    acknowledged (handle_or_drop)."""
    event_type, data, event_id = event_of(body)
    await handle_or_drop(
        handle(event_type, data, event_id, occurred_at(body)), event_type, event_id
    )
