"""Accounts' events (rule 11: each is safe to repeat and in any order; an error answers 5xx and
Pub/Sub delivers it again)."""

HANDLERS: dict = {}


async def handle(event_id: str, event_type: str, data: dict) -> None:
    """Other event types aren't accounts' (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(event_id, data)
