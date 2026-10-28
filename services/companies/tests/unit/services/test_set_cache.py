import asyncio
import time
import uuid

from companies.constants.interviews import SET_CACHE_SECONDS
from companies.integrations import library
from companies.services import set_cache


def test_a_sets_topics_are_read_once_for_many_page_views_and_again_once_expired(monkeypatch):
    reads = []
    set_id, other_id = uuid.uuid4(), uuid.uuid4()
    now = time.monotonic()

    async def get_set(read_id):
        reads.append(read_id)

        return {"id": str(read_id), "topics": [], "version": len(reads)}

    monkeypatch.setattr(library, "get_set", get_set)

    async def scenario():
        first = await set_cache.get_set(set_id)
        again = await set_cache.get_set(set_id)
        other = await set_cache.get_set(other_id)
        # Past SET_CACHE_SECONDS: a change in library (a question revealed) is read.
        monkeypatch.setattr(time, "monotonic", lambda: now + SET_CACHE_SECONDS + 1)
        later = await set_cache.get_set(set_id)

        return first, again, other, later

    first, again, other, later = asyncio.run(scenario())

    assert first == again and first["version"] == 1
    assert other["id"] == str(other_id)
    assert later["version"] == 3
    assert reads == [set_id, other_id, set_id]


def test_a_missing_set_isnt_kept(monkeypatch):
    reads = []

    async def missing(set_id):
        reads.append(set_id)

    monkeypatch.setattr(library, "get_set", missing)
    set_id = uuid.uuid4()

    async def scenario():
        return await set_cache.get_set(set_id), await set_cache.get_set(set_id)

    assert asyncio.run(scenario()) == (None, None)
    assert reads == [set_id, set_id]
