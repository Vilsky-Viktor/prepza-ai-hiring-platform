"""Integration tests' race helpers (services' tests/integration): a race test runs the real code
twice, keeps the first call's transaction open until the second is seen waiting on its lock in
Postgres, and only then lets the first commit. So the test proves the two transactions overlapped
on the lock, where a sleep or two calls at once only hope they did."""

import asyncio
import time
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from testee_common.db.db import sqlalchemy_url

LOCK_WAIT_TIMEOUT = 30.0
POLL_SECONDS = 0.02


class HeldCommit:
    """Wraps a module's Session factory: the first session it makes waits at its commit, or the
    first transaction it begins (`Session.begin()`, as services open one) waits before it
    commits, with its locks held, until `release` is set; `reached` is set once it waits there.
    Later ones commit as usual. Used as `monkeypatch.setattr(module, "Session", HeldCommit(...))`."""

    def __init__(self, factory):
        self.factory = factory
        self.reached = asyncio.Event()
        self.release = asyncio.Event()
        self.taken = False

    def first(self) -> bool:
        """Whether this is the first session or transaction made, the one held."""
        first = not self.taken
        self.taken = True

        return first

    def __call__(self, *args, **kwargs):
        session = self.factory(*args, **kwargs)

        if not self.first():
            return session

        commit = session.commit

        async def held_commit():
            self.reached.set()
            await self.release.wait()
            await commit()

        session.commit = held_commit

        return session

    def begin(self):
        return self.transaction(self.first())

    @asynccontextmanager
    async def transaction(self, held: bool):
        async with self.factory.begin() as session:
            yield session

            if held:
                self.reached.set()
                await self.release.wait()


def hold_first_commit(monkeypatch, module, name: str = "Session") -> HeldCommit:
    """The storage module's next session (from its factory `name`) waits at its commit until the
    race lets it go; pytest's `monkeypatch` puts the factory back after the test."""
    held = HeldCommit(getattr(module, name))
    monkeypatch.setattr(module, name, held)

    return held


async def wait_for_lock_wait(database_url: str, timeout: float = LOCK_WAIT_TIMEOUT) -> None:
    """Returns once a connection to this database waits on a lock (a row, a unique key being
    inserted, an advisory lock); fails when none does within `timeout` seconds."""
    deadline = time.monotonic() + timeout
    # Each check in its own transaction: Postgres lists pg_stat_activity's connections once per
    # transaction, so one open transaction never sees a connection opened after its first check
    # (the race's second call, when it's slow to connect).
    engine = create_async_engine(
        sqlalchemy_url(database_url), poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )
    waiting = text(
        "SELECT count(*) FROM pg_stat_activity"
        " WHERE datname = current_database() AND wait_event_type = 'Lock'"
    )

    try:
        async with engine.connect() as connection:
            while time.monotonic() < deadline:
                if await connection.scalar(waiting):
                    return

                await asyncio.sleep(POLL_SECONDS)
    finally:
        await engine.dispose()

    raise AssertionError("no transaction waited on a lock")


async def race(database_url: str, held: HeldCommit, first, second) -> tuple:
    """Runs `first` (a coroutine whose transaction `held` keeps open at its commit), then `second`
    once `first` waits there; lets `first` commit only once `second` waits on its lock. Returns
    both results, first's then second's; a call that raised gives its exception (a refusal such
    as OverLimit is a result)."""
    first_task = asyncio.create_task(first)
    reached = asyncio.create_task(held.reached.wait())
    await asyncio.wait({first_task, reached}, return_when=asyncio.FIRST_COMPLETED)

    if not held.reached.is_set():
        reached.cancel()
        # Its error, if it raised one.
        await first_task

        raise AssertionError("the first call ended without reaching its commit")

    second_task = asyncio.create_task(second)

    try:
        await wait_for_lock_wait(database_url)
    finally:
        held.release.set()

    return tuple(await asyncio.gather(first_task, second_task, return_exceptions=True))
