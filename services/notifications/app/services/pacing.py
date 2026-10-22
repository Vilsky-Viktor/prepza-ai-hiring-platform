import asyncio
import logging
import time

from prepza_common.rate_limit import counted

from app.constants.email import RESEND_PACE_KEY, RESEND_PER_SECOND
from app.integrations.redis import get_redis

logger = logging.getLogger(__name__)


async def wait_turn() -> None:
    """Waits until a request to Resend fits this second's RESEND_PER_SECOND, counted in Redis so
    invites, scheduled runs and bulk sends on every instance share it. With Redis down, it goes
    on unpaced: a 429 from Resend still goes back to be retried."""
    while True:
        second = int(time.time())

        try:
            total, _ = await counted(get_redis(), f"{RESEND_PACE_KEY}:{second}", 1, 2)
        except Exception:
            logger.warning("Resend's pacing skipped, Redis failed", exc_info=True)

            return

        if total <= RESEND_PER_SECOND:
            return

        await asyncio.sleep(max(0.0, second + 1 - time.time()))
