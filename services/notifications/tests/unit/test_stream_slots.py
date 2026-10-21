import asyncio

import anyio
import pytest
from fastapi import HTTPException
from prepza_common import memory_cache
from prepza_common.limit_list import LIMITS

from app.services import feed

MOST = LIMITS["STREAMS_PER_USER"].default


class FakeRedis:
    """Counters and their expiries, set in transactions as rate_limit.counted does."""

    def __init__(self, limits=None):
        self.counts = {}
        self.expiries = {}
        self.limits = limits or {}

    def pipeline(self, transaction):
        return Pipeline(self)

    async def hgetall(self, key):
        return {name.encode(): str(value).encode() for name, value in self.limits.items()}


class Pipeline:
    def __init__(self, redis):
        self.redis, self.steps = redis, []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def set(self, key, value, ex, nx):
        if key not in self.redis.counts:
            self.steps.append(lambda: self.redis.counts.setdefault(key, value))
            self.redis.expiries[key] = ex

    def incrby(self, key, amount):
        def run():
            self.redis.counts[key] = self.redis.counts.get(key, 0) + amount

            return self.redis.counts[key]

        self.steps.append(run)

    def ttl(self, key):
        self.steps.append(lambda: self.redis.expiries.get(key, -2))

    async def execute(self):
        # A round trip, as the real client's: a cancelled caller stops here.
        await asyncio.sleep(0)

        return [None] * (3 - len(self.steps)) + [step() for step in self.steps]


@pytest.fixture
def redis(monkeypatch):
    fake = FakeRedis()

    async def changes(user_id, fresh=False):
        yield ": connected\n\n"

    async def record_hit(name, **who):
        fake.hits = [*getattr(fake, "hits", []), (name, who)]

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr(feed, "get_redis", lambda: fake)
    monkeypatch.setattr(feed, "changes", changes)
    monkeypatch.setattr(feed, "record_hit", record_hit)

    return fake


async def read(stream):
    return [chunk async for chunk in stream]


def test_a_user_holds_a_limited_number_of_streams_and_a_closed_one_frees_its_slot(redis):
    async def scenario():
        streams = [await feed.open_stream("ann") for _ in range(MOST)]

        with pytest.raises(HTTPException) as refused:
            await feed.open_stream("ann")

        # Refused with when the bell tries again, and recorded.
        assert refused.value.status_code == 429
        assert int(refused.value.headers["Retry-After"]) > 0
        assert redis.hits == [("STREAMS_PER_USER", {"user_id": "ann"})]
        # Another user isn't held back by Ann's tabs.
        await read(await feed.open_stream("bob"))
        # One of Ann's streams ends: its slot is free again.
        await read(streams[0])

        return await feed.open_stream("ann")

    asyncio.run(scenario())

    assert redis.counts["streams:user:ann"] == MOST
    # The count never exists without its expiry.
    assert set(redis.expiries) == {"streams:user:ann", "streams:user:bob"}


def test_the_number_of_streams_is_as_edited_in_controls(redis):
    redis.limits["STREAMS_PER_USER"] = 1

    async def scenario():
        await feed.open_stream("ann")

        with pytest.raises(HTTPException):
            await feed.open_stream("ann")

    asyncio.run(scenario())


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
