"""The event loop's block logger: a blocked loop is logged once, with how long and where (files,
lines and functions, no values); a loop that isn't blocked logs nothing."""

import asyncio
import logging
import threading
import time

from prepza_common.observability import loop_watch
from prepza_common.observability.loop_watch import short_path, start_loop_watch

BLOCK = 0.2


async def logged(caplog, until: float = 5.0) -> list[str]:
    """The watcher's records, once one came (or `until` seconds passed)."""
    deadline = time.monotonic() + until

    while time.monotonic() < deadline and not caplog.records:
        await asyncio.sleep(0.02)

    return [record.getMessage() for record in caplog.records if record.name == loop_watch.__name__]


def blocking_call_with_a_secret(secret: str) -> None:
    time.sleep(BLOCK * 3)


def test_a_blocked_loop_is_logged_once_with_where(caplog):
    caplog.set_level(logging.WARNING, logger=loop_watch.__name__)

    async def scenario():
        stop = start_loop_watch(BLOCK)
        await asyncio.sleep(0.05)
        blocking_call_with_a_secret("hunter2")
        found = await logged(caplog)
        stop()

        return found

    [message] = asyncio.run(scenario())

    assert message.startswith("Event loop blocked for ")
    assert int(message.split(" for ")[1].split(" ms")[0]) >= BLOCK * 1000
    assert "test_loop_watch.py:" in message
    assert "blocking_call_with_a_secret" in message
    assert "hunter2" not in message


def test_a_loop_that_isnt_blocked_logs_nothing(caplog):
    caplog.set_level(logging.WARNING, logger=loop_watch.__name__)

    async def scenario():
        stop = start_loop_watch(BLOCK)
        found = await logged(caplog, until=BLOCK * 3)
        stop()

        return found

    assert asyncio.run(scenario()) == []


def test_a_late_beat_counts_only_while_the_loop_is_busy():
    """A throttled instance's beat comes late while its loop only waits in the selector: not
    blocked. The same late beat while code runs on the loop is."""

    async def scenario():
        watch = loop_watch.LoopWatch(BLOCK)
        # No beat for a while, as after Cloud Run throttled the instance.
        watch.beat -= 10
        thread = threading.Thread(target=watch.watching, daemon=True)
        thread.start()
        await asyncio.sleep(BLOCK * 2)
        waiting = watch.stuck_at
        blocking_call_with_a_secret("hunter2")
        busy = watch.stuck_at
        watch.stopped.set()
        thread.join()

        return waiting, busy

    waiting, busy = asyncio.run(scenario())

    assert waiting is None
    assert "blocking_call_with_a_secret" in busy


def test_a_path_is_named_from_its_package_on():
    assert short_path("/services/rounds/.venv/lib/python3.14/site-packages/httpx/_client.py") == (
        "httpx/_client.py"
    )
    assert short_path("/services/rounds/src/rounds/services/practice.py") == (
        "rounds/services/practice.py"
    )
    assert short_path("<frozen importlib._bootstrap>") == "<frozen importlib._bootstrap>"
