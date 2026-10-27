from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events.pubsub import PushBody, event_of, occurred_at

from app.services.usage_events import handle

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes the services' records of AI calls and limit hits here."""
    event_type, data, event_id = event_of(body)
    await handle(event_type, data, event_id, occurred_at(body))
