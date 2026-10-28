"""Accounts' events: companies' deleted guests (rule 11: each is safe to repeat and in any order;
an error answers 5xx and Pub/Sub delivers it again)."""

from accounts.constants.events import GUESTS_DELETED
from accounts.handlers import guests_deleted

HANDLERS = {
    GUESTS_DELETED: guests_deleted.handle,
}


async def handle(event_id: str, event_type: str, data: dict) -> None:
    """Other event types aren't accounts' (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(event_id, data)
