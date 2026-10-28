"""Steps of one action are saved together: when a later step fails, the earlier ones aren't
saved either (python-services.md: each action is a single save)."""

import pytest

from generation.constants.quality import QualityFlag
from generation.integrations.redis import get_redis
from generation.repositories import patterns
from generation.services import patterns as job
from tests.integration.services.test_patterns import cleanup, flag_name, given
from tests.integration.transactions import transaction
from tests.unit.services.test_pattern_checks import signal
from tests.unit.services.test_pattern_job import found


@pytest.fixture(autouse=True)
def fresh_redis():
    get_redis.cache_clear()


def test_a_known_pattern_found_again_isnt_counted_when_a_new_one_fails_to_save(run, monkeypatch):
    flag = flag_name(QualityFlag.REWRITE)
    rule = "Two options say the same thing in different words."
    given(
        monkeypatch,
        flag,
        [found("Reworded", [1, 2, 3], same_as=1), found("The stem gives the answer away.", [1, 2])],
    )
    signals = [signal(f"Question number {i}?", flag=flag) for i in range(3)]

    async def broken(*args):
        raise RuntimeError("The database went away")

    async def scenario():
        await cleanup(flag)

        try:
            await transaction(patterns.add, rule, flag, 2)
            monkeypatch.setattr(patterns, "add", broken)

            with pytest.raises(RuntimeError):
                await job.propose(flag, signals)

            return await transaction(patterns.for_flag, flag)
        finally:
            await cleanup(flag)

    [known] = run(scenario())

    assert (known.text, known.question_count) == (rule, 2)
