"""Generation's events: accounts' deleted accounts (rule 11: deleting again deletes nothing
more, so a redelivery or a repeat is safe, in any order; an error answers 5xx and Pub/Sub
delivers the event again)."""

from prepza_common.events.deletions import USER_DELETED

from generation.handlers import user_deleted

HANDLERS = {USER_DELETED: user_deleted.handle}


async def handle(event_type: str, data: dict) -> None:
    """Other event types aren't generation's (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data)
