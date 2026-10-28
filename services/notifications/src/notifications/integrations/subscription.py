"""The instance's one Redis subscription to every bell's channel, shared by its open tabs: each
tab waits on an event of its own, set when one of its channels hears something. However many tabs
are open, an instance holds one Redis connection for them (Cloud NAT allows only so many to one
address). It's made with the first tab and dropped with the last."""

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from prepza_common.http.backoff import wait_seconds

from notifications.constants.notifications import CHANNELS, HEARTBEAT_SECONDS, RESUBSCRIBE_SECONDS
from notifications.integrations.redis import get_redis

logger = logging.getLogger(__name__)


class Subscription:
    def __init__(self) -> None:
        # Each channel's listening tabs.
        self.tabs: dict[str, set[asyncio.Event]] = defaultdict(set)
        self.ready = asyncio.Event()
        self.task = asyncio.create_task(self.read())

    async def read(self) -> None:
        """Passes each message on to its channel's tabs. A lost connection is made again; then
        every tab hears, as it may have missed something."""
        lost = False

        while True:
            pubsub = get_redis().pubsub()

            try:
                await pubsub.psubscribe(CHANNELS)
                self.ready.set()

                if lost:
                    self.wake(*self.tabs)

                while True:
                    message = await pubsub.get_message(timeout=HEARTBEAT_SECONDS)

                    if message is None:
                        # Keeps a quiet connection open through Cloud NAT, and finds a dead one.
                        await pubsub.ping()
                    elif message["type"] == "pmessage":
                        self.wake(message["channel"].decode())
            except Exception:
                logger.warning("Lost the bell's Redis subscription", exc_info=True)
                lost = True
            finally:
                await pubsub.aclose()

            # Jittered, so every instance doesn't reconnect at once when Redis comes back.
            await asyncio.sleep(wait_seconds(RESUBSCRIBE_SECONDS, 0))

    def wake(self, *channels: str) -> None:
        for channel in channels:
            for tab in self.tabs.get(channel, ()):
                tab.set()


shared: Subscription | None = None


@asynccontextmanager
async def listening(channels: list[str]) -> AsyncIterator[asyncio.Event]:
    """An event for one tab, set whenever one of `channels` hears something; the tab clears it."""
    global shared

    if shared is None:
        shared = Subscription()

    subscription = shared
    heard = asyncio.Event()

    for channel in channels:
        subscription.tabs[channel].add(heard)

    try:
        await asyncio.wait_for(subscription.ready.wait(), HEARTBEAT_SECONDS)

        yield heard
    finally:
        for channel in channels:
            subscription.tabs[channel].discard(heard)

            if not subscription.tabs[channel]:
                del subscription.tabs[channel]

        if not subscription.tabs and shared is subscription:
            subscription.task.cancel()
            shared = None
