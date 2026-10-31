import asyncio

from testee_common.db import paging


def test_every_id_is_read_a_page_at_a_time_until_a_short_page(monkeypatch):
    monkeypatch.setattr(paging, "ID_PAGE_SIZE", 2)
    ids = ["a", "b", "c", "d", "e"]
    asked = []

    async def read_page(after):
        asked.append(after)
        rest = [item for item in ids if item > after]

        return rest[:2]

    assert asyncio.run(paging.every_id(read_page)) == ids
    assert asked == ["", "b", "d"]


def test_a_full_last_page_is_followed_by_an_empty_one(monkeypatch):
    monkeypatch.setattr(paging, "ID_PAGE_SIZE", 2)

    async def read_page(after):
        return {"": ["a", "b"], "b": []}[after]

    assert asyncio.run(paging.every_id(read_page)) == ["a", "b"]
