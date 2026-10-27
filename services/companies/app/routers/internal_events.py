from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events.pubsub import PushBody, event_of, occurred_at

from app.services import audit_events, candidate_billing, generation_events

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Invoker])
async def receive_event(body: PushBody) -> None:
    """Pub/Sub pushes every event here. A failure answers with an error, so Pub/Sub retries it,
    and moves it to the dead-letter topic after the subscription's maximum attempts."""
    event_type, data, event_id = event_of(body)
    await generation_events.handle(event_type, data, event_id)
    await candidate_billing.handle(event_type, data, event_id)
    await audit_events.handle(event_type, data, event_id, occurred_at(body))
