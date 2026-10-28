"""Pub/Sub's pushes for the services' tests of their /internal/events (each service's pytest
`pythonpath` includes this folder)."""

from prepza_common.events import pubsub


def push(event_type: str, data: dict, event_id: str = "e-1") -> dict:
    """A push of one event, as the emulator sends it (no token)."""
    message = pubsub.message(event_type, data, event_id)

    return {
        "message": {**message, "messageId": "m-1"},
        "subscription": "projects/demo-test/subscriptions/test-events",
    }


def failing_handler(monkeypatch, events_module, error: Exception) -> None:
    """The service's event handling, in its events route's module, failing with `error`."""

    async def handle(*args, **kwargs):
        raise error

    monkeypatch.setattr(events_module, "handle", handle)
