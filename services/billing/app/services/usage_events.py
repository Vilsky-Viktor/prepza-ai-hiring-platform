"""Billing's events: every AI call and limit hit the services record (rule 11: a redelivered
event finds its id stored and changes nothing; each row keeps its own time, so order doesn't
matter; an error answers 5xx and Pub/Sub delivers it again)."""

import logging
from datetime import datetime

from prepza_common.ai.ai_cap import add_unpaid
from prepza_common.ai.ai_constants import AI_USED, LIMIT_HIT, Category

from app.integrations.redis import get_redis
from app.storage import usage

logger = logging.getLogger(__name__)

UNPAID = (Category.UNPAID, Category.NO_COMPANY)


async def handle(event_type: str, data: dict, event_id: str, occurred_at: datetime) -> None:
    """Other event types aren't billing's (locally every subscription gets every event)."""
    if event_type == LIMIT_HIT:
        await usage.store_hit(event_id, occurred_at, data)

        return

    if event_type != AI_USED:
        return

    category = await usage.store_usage(event_id, occurred_at, data)

    if category not in UNPAID or not data.get("cost_usd"):
        return

    # Stored once, so counted once; with Redis down the cap misses this call rather than the
    # event being stored twice.
    try:
        await add_unpaid(get_redis(), data["cost_usd"])
    except Exception:
        logger.warning("Unpaid AI spend not counted, Redis failed", exc_info=True)
