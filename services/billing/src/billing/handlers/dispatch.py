"""Billing's events: every AI call and limit hit the services record (rule 11: a redelivered
event finds its id stored and changes nothing; each row keeps its own time, so order doesn't
matter; an error answers 5xx and Pub/Sub delivers it again)."""

from datetime import datetime

from prepza_common.ai.ai_constants import AI_USED, LIMIT_HIT

from billing.handlers import ai_used, limit_hit

HANDLERS = {AI_USED: ai_used.handle, LIMIT_HIT: limit_hit.handle}


async def handle(event_type: str, data: dict, event_id: str, occurred_at: datetime) -> None:
    """Other event types aren't billing's (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data, event_id, occurred_at)
