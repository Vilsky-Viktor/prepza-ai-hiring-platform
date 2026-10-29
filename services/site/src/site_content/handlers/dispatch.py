"""Site's events: accounts' deleted accounts and generation's news translations (rule 11:
deleting again deletes nothing more, and a translation saved again replaces itself, so a
redelivery or a repeat is safe, in any order; an error answers 5xx and Pub/Sub delivers the
event again)."""

from prepza_common.events.deletions import USER_DELETED
from prepza_common.events.news import NEWS_TRANSLATED

from site_content.handlers import news_translated, user_deleted

HANDLERS = {USER_DELETED: user_deleted.handle, NEWS_TRANSLATED: news_translated.handle}


async def handle(event_type: str, data: dict) -> None:
    """Other event types aren't site's (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data)
