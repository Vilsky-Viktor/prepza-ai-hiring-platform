# The emergency pause (internal_docs/compliance/post-market-monitoring-plan.md, section 4): a superadmin
# turns it on, and every service refuses new candidate interviews and invites, practice rounds,
# previews, AI generation and the help chat (the plan lists exactly what). Sessions already
# running may finish: answering is never refused. The switch is
# one Redis key without expiry, which every service already reads for its rate limits.
import logging

from fastapi import status
from prepza_common.config.constants import PAUSE_CACHE_SECONDS, PAUSE_KEY, PAUSED
from prepza_common.i18n import error_codes
from prepza_common.i18n.i18n import CodedError
from prepza_common.limits import switches
from prepza_common.limits.limit_list import PAUSED_LIMIT
from prepza_common.limits.limits import EVERYONE, record_hit

logger = logging.getLogger(__name__)


async def is_paused(redis) -> bool:
    """Read at most every PAUSE_CACHE_SECONDS per instance; with Redis down, the last state this
    instance read (switches.is_on)."""
    return await switches.is_on(redis, PAUSE_KEY, PAUSE_CACHE_SECONDS)


async def refuse_if_paused(
    redis, what: str, company_id: object | None = None, user_id: str | None = None
) -> None:
    """Refuses `what` (a short name of what was asked, such as "help_chat") while paused, and
    records the refusal like a limit's."""
    if await is_paused(redis):
        kept = {"company_id": company_id, "user_id": user_id, "what": what}
        await record_hit(PAUSED_LIMIT, scope=EVERYONE, **kept)

        raise CodedError(status.HTTP_503_SERVICE_UNAVAILABLE, PAUSED, error_codes.PAUSED)


async def set_paused(redis, paused: bool, user_id: str) -> None:
    """Who switched it and when is kept in the logs."""
    if paused:
        await redis.set(PAUSE_KEY, user_id)
    else:
        await redis.delete(PAUSE_KEY)

    switches.remember(PAUSE_KEY, paused, PAUSE_CACHE_SECONDS)
    logger.warning("Emergency pause turned %s by superadmin %s", "on" if paused else "off", user_id)
