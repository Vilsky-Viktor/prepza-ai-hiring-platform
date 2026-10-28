import logging

from prepza_common.redis import memory_cache

from rounds.constants.rounds import SET_CACHE_SECONDS
from rounds.helpers.sessions import session_out
from rounds.integrations import library
from rounds.models.sessions import Session
from rounds.schemas.sessions import SessionOut

logger = logging.getLogger(__name__)


async def session_out_titled(row: Session) -> SessionOut:
    """The section with its interview's title and language, kept for a little while; without
    them when library can't say now, so the candidate's interview goes on."""
    key = f"set:{row.interview_set_id}"
    found = memory_cache.get(key)

    if found is None:
        try:
            found = await library.get_set(row.interview_set_id)
        except Exception:
            logger.warning(
                "No title for set %s: library didn't answer", row.interview_set_id, exc_info=True
            )

        if found is None:
            return session_out(row)

        found = {"title": found["title"], "language": found.get("language")}
        memory_cache.put(key, found, SET_CACHE_SECONDS)

    return session_out(row, found["title"], found["language"])
