import logging
from datetime import datetime

from prepza_common.ai.ai_cap import add_unpaid
from prepza_common.ai.ai_constants import Category

from billing.integrations.redis import get_redis
from billing.services import usage

logger = logging.getLogger(__name__)

UNPAID = (Category.UNPAID, Category.NO_COMPANY)


async def handle(data: dict, event_id: str, occurred_at: datetime) -> None:
    """An AI call, kept once by its event id; one nobody pays for counts against the cap on
    unpaid AI spend."""
    category = await usage.record_usage(event_id, occurred_at, data)

    if category not in UNPAID or not data.get("cost_usd"):
        return

    # Stored once, so counted once; with Redis down the cap misses this call rather than the
    # event being stored twice.
    try:
        await add_unpaid(get_redis(), data["cost_usd"])
    except Exception:
        logger.warning("Unpaid AI spend not counted, Redis failed", exc_info=True)
