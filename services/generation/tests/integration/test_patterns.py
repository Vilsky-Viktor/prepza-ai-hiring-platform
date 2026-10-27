"""The weekly pattern job and the patterns tab against the real database and Redis (database 15):
what a run stores, a second run in the same week, and a superadmin's review."""

import pytest
from prepza_common.events import pubsub
from sqlalchemy import delete, inspect

from app.constants.patterns import PATTERN_DONE_KEY, PatternStatus
from app.constants.quality import QualityFlag
from app.integrations import library, llm
from app.integrations.redis import get_redis
from app.models.patterns import QualityPattern
from app.services import patterns as job
from app.storage import patterns
from app.storage.db import Session, engine
from tests.unit.test_pattern_checks import signal
from tests.unit.test_pattern_job import Model, found


@pytest.fixture(autouse=True)
def no_events(monkeypatch):
    """The run's AI cost isn't published: it would reach the local billing's records."""

    async def publish_batch(messages, timeout=None):
        pass

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)
    get_redis.cache_clear()


def flag_name(flag: QualityFlag) -> str:
    """A flag of the test's own (each test takes another), so no other test's row or Redis key
    is touched; the database allows only real flags."""
    return str(flag)


async def cleanup(flag):
    async with Session() as session:
        await session.execute(delete(QualityPattern).where(QualityPattern.flag == flag))
        await session.commit()

    await get_redis().delete(PATTERN_DONE_KEY.format(flag=flag))
    get_redis.cache_clear()


def given(monkeypatch, flag, *answers):
    signals = [signal(f"Question number {i}?", flag=flag) for i in range(3)]

    async def quality_signals(days):
        return signals

    model = Model(list(answers))
    monkeypatch.setattr(library, "quality_signals", quality_signals)
    monkeypatch.setattr(llm, "get_patterns_llm", lambda: model)

    return model


def test_the_table_holds_no_question_id_or_text(run):
    async def columns():
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync: [c["name"] for c in inspect(sync).get_columns("quality_patterns")]
            )

    assert sorted(run(columns())) == sorted(
        [
            "id",
            "text",
            "flag",
            "question_count",
            "first_seen",
            "last_seen",
            "status",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
    )


def test_a_run_stores_a_proposed_pattern_and_a_second_run_that_week_counts_nothing(
    run, monkeypatch
):
    flag = flag_name(QualityFlag.WRONG_KEY)
    rule = "Two options say the same thing in different words."
    model = given(monkeypatch, flag, [found(rule, [1, 2])], [found(rule, [1, 2, 3])])

    async def scenario():
        try:
            await job.run()
            await job.run()
            done = await get_redis().exists(PATTERN_DONE_KEY.format(flag=flag))

            return await patterns.for_flag(flag), done
        finally:
            await cleanup(flag)

    [stored], done = run(scenario())

    assert (stored.text, stored.question_count, stored.status) == (
        rule,
        2,
        PatternStatus.PROPOSED,
    )
    assert stored.first_seen == stored.last_seen
    assert done == 1
    assert len(model.prompts) == 1


def test_a_pattern_found_again_next_week_adds_to_its_count_and_last_seen(run, monkeypatch):
    flag = flag_name(QualityFlag.REWRITE)
    rule = "Two options say the same thing in different words."
    given(monkeypatch, flag, [found(rule, [1, 2])], [found("Reworded", [1, 2, 3], same_as=1)])

    async def scenario():
        try:
            await job.run()
            # A week later: the flag's "done" key has expired.
            await get_redis().delete(PATTERN_DONE_KEY.format(flag=flag))
            await job.run()

            return await patterns.for_flag(flag)
        finally:
            await cleanup(flag)

    [stored] = run(scenario())

    assert (stored.text, stored.question_count) == (rule, 5)
    assert stored.last_seen > stored.first_seen


def test_a_superadmins_review_is_kept_with_who_and_when_once(run):
    flag = flag_name(QualityFlag.WEAK_OPTIONS)

    async def scenario():
        try:
            await patterns.add("The scenario leaves out a detail.", flag, 3)
            [pattern] = await patterns.for_flag(flag)
            first = await patterns.review(pattern.id, PatternStatus.DISMISSED, "ann")
            again = await patterns.review(pattern.id, PatternStatus.APPROVED, "bob")
            dismissed = await patterns.by_status(PatternStatus.DISMISSED, 0, 1000)
            proposed = await patterns.by_status(PatternStatus.PROPOSED, 0, 1000)

            return pattern.id, first, again, dismissed, proposed
        finally:
            await cleanup(flag)

    pattern_id, first, again, dismissed, proposed = run(scenario())

    assert (first, again) == (True, False)
    [kept] = [row for row in dismissed if row.id == pattern_id]
    assert (kept.status, kept.reviewed_by) == (PatternStatus.DISMISSED, "ann")
    assert kept.reviewed_at is not None
    assert pattern_id not in [row.id for row in proposed]
