import asyncio

import anyio
import pytest
from fastapi import HTTPException

from app.constants.notifications import MAX_STREAMS_PER_USER
from app.services import feed


class FakeRedis:
    def __init__(self):
        self.counts = {}
        self.expiries = []

    async def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1

        return self.counts[key]

    async def decr(self, key):
        # A round trip, as the real client's: a cancelled caller stops here.
        await asyncio.sleep(0)
        self.counts[key] -= 1

    async def expire(self, key, seconds):
        self.expiries.append(key)


@pytest.fixture
def redis(monkeypatch):
    fake = FakeRedis()

    async def changes(user_id, fresh=False):
        yield ": connected\n\n"

    monkeypatch.setattr(feed, "get_redis", lambda: fake)
    monkeypatch.setattr(feed, "changes", changes)

    return fake


async def read(stream):
    return [chunk async for chunk in stream]


def test_a_user_holds_a_limited_number_of_streams_and_a_closed_one_frees_its_slot(redis):
    async def scenario():
        streams = [await feed.open_stream("ann") for _ in range(MAX_STREAMS_PER_USER)]

        with pytest.raises(HTTPException) as refused:
            await feed.open_stream("ann")

        assert refused.value.status_code == 429
        # Another user isn't held back by Ann's tabs.
        await read(await feed.open_stream("bob"))
        # One of Ann's streams ends: its slot is free again.
        await read(streams[0])

        return await feed.open_stream("ann")

    asyncio.run(scenario())

    assert redis.counts["streams:user:ann"] == MAX_STREAMS_PER_USER


def test_a_tab_closed_mid_stream_frees_its_slot(redis, monkeypatch):
    connected = asyncio.Event()

    async def changes(user_id, fresh=False):
        yield ": connected\n\n"
        await asyncio.Event().wait()

    monkeypatch.setattr(feed, "changes", changes)

    async def read_until_closed(stream):
        async for _ in stream:
            connected.set()

    async def scenario():
        stream = await feed.open_stream("ann")

        # The server cancels the response when the tab goes, as Starlette does on a disconnect.
        async with anyio.create_task_group() as tasks:
            tasks.start_soon(read_until_closed, stream)
            await connected.wait()
            tasks.cancel_scope.cancel()

    asyncio.run(scenario())

    assert redis.counts["streams:user:ann"] == 0


def test_a_refused_tab_does_not_renew_the_slots(redis):
    async def scenario():
        for _ in range(MAX_STREAMS_PER_USER):
            await feed.open_stream("ann")

        with pytest.raises(HTTPException):
            await feed.open_stream("ann")

    asyncio.run(scenario())

    assert len(redis.expiries) == MAX_STREAMS_PER_USER
