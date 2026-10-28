import asyncio

import pytest

from notifications.integrations import subscription
from notifications.integrations.subscription import listening


class FakePubSub:
    """Redis' pub/sub connection: get_message hands out what the test puts in `inbox`."""

    def __init__(self, inbox: asyncio.Queue) -> None:
        self.inbox = inbox

    async def psubscribe(self, pattern):
        pass

    async def get_message(self, timeout):
        item = await self.inbox.get()

        if isinstance(item, Exception):
            raise item

        return item

    async def ping(self):
        pass

    async def aclose(self):
        pass


@pytest.fixture
def redis(monkeypatch):
    """How many subscriptions were made, and the inbox they read from."""
    found = {"subscriptions": 0, "inbox": None}

    class FakeRedis:
        def pubsub(self):
            found["subscriptions"] += 1

            return FakePubSub(found["inbox"])

    monkeypatch.setattr(subscription, "get_redis", FakeRedis)
    monkeypatch.setattr(subscription, "RESUBSCRIBE_SECONDS", 0)

    return found


def pmessage(channel: str) -> dict:
    return {"type": "pmessage", "channel": channel.encode(), "data": b"new"}


async def settle():
    for _ in range(5):
        await asyncio.sleep(0)


def test_tabs_share_one_subscription_and_hear_only_their_channels(redis):
    async def scenario():
        redis["inbox"] = asyncio.Queue()

        async with listening(["a", "b"]) as first, listening(["b"]) as second:
            await redis["inbox"].put(pmessage("a"))
            await settle()
            heard_a = (first.is_set(), second.is_set())
            first.clear()
            await redis["inbox"].put(pmessage("b"))
            await settle()

            return heard_a, (first.is_set(), second.is_set())

    assert asyncio.run(scenario()) == ((True, False), (True, True))
    assert redis["subscriptions"] == 1
    # Gone with the last tab.
    assert subscription.shared is None


def test_a_lost_subscription_is_made_again_and_wakes_every_tab(redis):
    async def scenario():
        redis["inbox"] = asyncio.Queue()

        async with listening(["a"]) as tab:
            await redis["inbox"].put(ConnectionError("Redis went away"))
            await settle()

            return tab.is_set()

    # The tab may have missed a notification meanwhile, so it reloads.
    assert asyncio.run(scenario()) is True
    assert redis["subscriptions"] == 2
