import asyncio

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
