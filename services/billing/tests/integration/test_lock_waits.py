"""The race helper's check (prepza_common.db.lock_waits) sees a lock wait on a connection opened after
it started looking, as when a race's second call is slow to connect."""

import asyncio
import os

from prepza_common.db import lock_waits
from prepza_common.db.db import sqlalchemy_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

LOCK_KEY = 4_242_001


def test_a_lock_wait_that_begins_after_the_first_check_is_seen(run, monkeypatch):
    database_url = os.environ["DATABASE_URL"]
    checked = asyncio.Event()
    sleep = asyncio.sleep

    async def note_check(seconds):
        # The check's own pause between looks, not the driver's.
        if seconds == lock_waits.POLL_SECONDS:
            checked.set()

        await sleep(seconds)

    monkeypatch.setattr(lock_waits.asyncio, "sleep", note_check)

    async def scenario():
        engine = create_async_engine(sqlalchemy_url(database_url), poolclass=NullPool)

        async with engine.connect() as holder:
            await holder.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
            looking = asyncio.create_task(lock_waits.wait_for_lock_wait(database_url, 5.0))
            # The check has looked at least once before the waiting connection even opens.
            await checked.wait()

            async with engine.connect() as waiter:
                waiting = asyncio.create_task(
                    waiter.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
                )

                try:
                    await looking
                finally:
                    unlock = text("SELECT pg_advisory_unlock(:key)")
                    await holder.execute(unlock, {"key": LOCK_KEY})
                    await waiting
                    await waiter.execute(unlock, {"key": LOCK_KEY})

        await engine.dispose()

    run(scenario())
