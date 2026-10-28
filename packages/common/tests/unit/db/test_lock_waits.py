import asyncio
from contextlib import asynccontextmanager

from prepza_common.db.lock_waits import HeldCommit


class FakeSession:
    def __init__(self, log: list[str], name: str):
        self.log = log
        self.name = name

    async def commit(self):
        self.log.append(self.name)


def test_only_the_first_session_waits_at_its_commit_until_released():
    log = []
    names = iter(["first", "second"])

    async def scenario():
        held = HeldCommit(lambda: FakeSession(log, next(names)))
        first, second = held(), held()
        committing = asyncio.create_task(first.commit())
        await held.reached.wait()
        await second.commit()
        before = list(log)
        held.release.set()
        await committing

        return before

    assert asyncio.run(scenario()) == ["second"]
    assert log == ["second", "first"]


class FakeFactory:
    """A session factory whose transactions (`begin()`) note their name when they commit."""

    def __init__(self, log: list[str], names):
        self.log = log
        self.names = names

    @asynccontextmanager
    async def begin(self):
        name = next(self.names)

        yield name

        self.log.append(name)


def test_only_the_first_transaction_waits_before_it_commits_until_released():
    log = []

    async def scenario():
        held = HeldCommit(FakeFactory(log, iter(["first", "second"])))

        async def run():
            async with held.begin() as name:
                return name

        committing = asyncio.create_task(run())
        await held.reached.wait()
        await run()
        before = list(log)
        held.release.set()

        return before, await committing

    assert asyncio.run(scenario()) == (["second"], "first")
    assert log == ["second", "first"]
