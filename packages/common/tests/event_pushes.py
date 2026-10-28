"""Pub/Sub's pushes for the services' tests of their /internal/events (each service's pytest
`pythonpath` includes this folder): the one builder every service's tests use, never a copy."""

from datetime import datetime

from prepza_common.config.constants import EVENT_ID_ATTRIBUTE
from prepza_common.events import pubsub


def push(
    event_type: str,
    data: dict,
    event_id: str | None = "e-1",
    message_id: str = "m-1",
    occurred_at: datetime | None = None,
) -> dict:
    """A push of one event, as the emulator sends it (no token). Without `event_id` it carries
    none, as an event published before the attribute existed, and Pub/Sub's `message_id` stands
    for it (pubsub.event_of)."""
    message = pubsub.message(event_type, data, event_id, occurred_at)

    if event_id is None:
        del message["attributes"][EVENT_ID_ATTRIBUTE]

    return {
        "message": {**message, "messageId": message_id},
        "subscription": "projects/demo-test/subscriptions/test-events",
    }


def failing_handler(monkeypatch, events_module, error: Exception) -> None:
    """The service's event handling, in its events route's module, failing with `error`."""

    async def handle(*args, **kwargs):
        raise error

    monkeypatch.setattr(events_module, "handle", handle)
