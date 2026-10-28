import asyncio
import uuid

import httpx
import pytest
from prepza_common.events.notifications import Recipient
from prepza_common.redis import memory_cache

from notifications.integrations import companies
from notifications.services import feed


@pytest.fixture
def asked(monkeypatch):
    """Companies, counting its answers; `down` makes it fail."""
    state = {"calls": 0, "down": False, "ids": ["c1"]}

    async def company_ids(user_id):
        state["calls"] += 1

        if state["down"]:
            raise httpx.ConnectError("companies is down")

        return list(state["ids"])

    monkeypatch.setattr(companies, "company_ids", company_ids)

    return state


def test_a_users_companies_are_kept_a_minute_and_read_again_when_fresh(asked):
    user = f"u-{uuid.uuid4()}"

    first, _ = asyncio.run(feed.recipients_of(user))
    asked["ids"] = ["c1", "c2"]
    kept, _ = asyncio.run(feed.recipients_of(user))
    fresh, _ = asyncio.run(feed.recipients_of(user, fresh=True))

    assert asked["calls"] == 2
    assert kept == first == [(Recipient.USER, user), (Recipient.COMPANY, "c1")]
    assert (Recipient.COMPANY, "c2") in fresh


def test_with_companies_down_the_user_still_hears_their_own(asked):
    user = f"u-{uuid.uuid4()}"
    asked["down"] = True

    recipients, complete = asyncio.run(feed.recipients_of(user))

    assert recipients == [(Recipient.USER, user)]
    assert complete is False
    # Nothing is kept from a failed read: the next one asks again.
    assert memory_cache.get(f"notifications:company-ids:{user}") is None


def test_a_stream_ends_after_its_time_so_the_tab_reconnects(asked, monkeypatch):
    clock = {"now": 0.0}

    class Heard:
        def clear(self):
            pass

        async def wait(self):
            # Nothing comes: each wait is a heartbeat that moves the clock 100 seconds on.
            clock["now"] += 100
            raise TimeoutError

    class Listening:
        async def __aenter__(self):
            return Heard()

        async def __aexit__(self, *args):
            return False

    async def wait_for(awaitable, timeout):
        return await awaitable

    monkeypatch.setattr(feed.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(feed.asyncio, "wait_for", wait_for)
    monkeypatch.setattr(feed, "listening", lambda channels: Listening())

    async def collect(user):
        return [chunk async for chunk in feed.changes(user)]

    full = asyncio.run(collect(f"u-{uuid.uuid4()}"))
    asked["down"] = True
    clock["now"] = 0.0
    partial = asyncio.run(collect(f"u-{uuid.uuid4()}"))

    # 300 seconds with the companies, 60 without: then the stream ends.
    assert full.count(": heartbeat\n\n") == 3
    assert partial.count(": heartbeat\n\n") == 1
