from prepza_common.redis import memory_cache

from app.constants.interviews import SET_CACHE_SECONDS
from app.integrations import library


async def get_set(set_id) -> dict | None:
    """The set's title and topics with their question counts, for the test's page: kept for
    SET_CACHE_SECONDS; a missing set isn't kept."""
    key = f"set:{set_id}"
    found = memory_cache.get(key)

    if found is None:
        found = await library.get_set(set_id)

        if found is not None:
            memory_cache.put(key, found, SET_CACHE_SECONDS)

    return found
