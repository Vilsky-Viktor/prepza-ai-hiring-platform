"""The weekly pattern job (services/patterns.py): last week's flagged and replaced questions, by
flag, turned into proposed general rules. Storage here is in memory; the database's side is in
tests/integration/test_patterns.py."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from prepza_common.ai_constants import AI_USED

from app.constants.actions import QUALITY_PATTERNS
from app.constants.patterns import (
    MAX_PATTERN_QUESTIONS,
    PATTERN_DONE_KEY,
    PATTERN_LOCK_KEY,
    PatternStatus,
)
from app.integrations import library, llm
from app.schemas.patterns import ProposedPattern, ProposedPatterns
from app.services import patterns as job
from app.storage import patterns as storage
from tests.unit.fake_ai import Chat, reply
from tests.unit.test_pattern_checks import signal

RULE = "Two options say the same thing in different words."
OTHER_RULE = "The scenario leaves out the detail that decides the answer."


class Model:
    """The model: one call a run, answering with the next of `answers` (a list of patterns), and
    the prompts it was given."""

    def __init__(self, answers):
        self.answers = answers
        self.prompts = []
        self.chat = Chat(replies=[reply(1000, 100) for _ in answers])

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        self.prompts.append(messages[0].content)
        await self.chat.ainvoke(messages)

        return ProposedPatterns(patterns=self.answers.pop(0))


@pytest.fixture
def stored(monkeypatch):
    """The patterns table in memory, as a list of rows."""
    rows = []

    async def for_flag(flag):
        return [row for row in rows if row.flag == flag]

    async def add(text, flag, question_count):
        rows.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                text=text,
                flag=flag,
                question_count=question_count,
                status=PatternStatus.PROPOSED,
                seen_again=0,
            )
        )

    async def seen(pattern_id, question_count):
        [row] = [row for row in rows if row.id == pattern_id]
        row.question_count += question_count
        row.seen_again += 1

    monkeypatch.setattr(storage, "for_flag", for_flag)
    monkeypatch.setattr(storage, "add", add)
    monkeypatch.setattr(storage, "seen", seen)

    return rows


@pytest.fixture
def redis(redis, monkeypatch):
    monkeypatch.setattr(job, "get_redis", lambda: redis)

    return redis


def given(monkeypatch, signals, *answers):
    async def quality_signals(days):
        return signals

    model = Model(list(answers))
    monkeypatch.setattr(library, "quality_signals", quality_signals)
    monkeypatch.setattr(llm, "get_verifier_llm", lambda: model)

    return model


def found(text, questions, same_as=None):
    return ProposedPattern(text=text, questions=questions, same_as=same_as)


def flagged(count, flag="rewrite"):
    return [signal(f"Question number {i}?", flag=flag) for i in range(count)]


def test_a_mistake_in_two_questions_is_stored_as_proposed(monkeypatch, stored, redis):
    given(monkeypatch, flagged(3), [found(f"  {RULE} ", [1, 3])])

    asyncio.run(job.run())

    [row] = stored
    assert (row.text, row.flag, row.question_count, row.status) == (
        RULE,
        "rewrite",
        2,
        PatternStatus.PROPOSED,
    )


def test_a_mistake_in_one_question_or_in_numbers_not_given_is_left_out(monkeypatch, stored, redis):
    given(monkeypatch, flagged(3), [found(RULE, [2]), found(OTHER_RULE, [1, 4, 0])])

    asyncio.run(job.run())

    assert stored == []


def test_questions_are_grouped_by_flag_one_call_each(monkeypatch, stored, redis):
    signals = flagged(2, "wrong_key") + flagged(2, "rewrite")
    model = given(monkeypatch, signals, [found(RULE, [1, 2])], [found(OTHER_RULE, [1, 2])])

    asyncio.run(job.run())

    assert [(row.flag, row.text) for row in stored] == [
        ("wrong_key", RULE),
        ("rewrite", OTHER_RULE),
    ]
    assert len(model.prompts) == 2


def test_a_flag_with_a_single_question_isnt_sent_to_the_model(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(1, "wrong_key") + flagged(2), [found(RULE, [1, 2])])

    asyncio.run(job.run())

    assert len(model.prompts) == 1
    assert [row.flag for row in stored] == ["rewrite"]


def test_the_model_reads_at_most_the_limit_of_one_flags_questions(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(MAX_PATTERN_QUESTIONS + 5), [found(RULE, [1, 61, 62])])

    asyncio.run(job.run())

    assert (
        f"{MAX_PATTERN_QUESTIONS}. Question number {MAX_PATTERN_QUESTIONS - 1}?"
        in (model.prompts[0])
    )
    assert f"Question number {MAX_PATTERN_QUESTIONS}?" not in model.prompts[0]
    # Numbers past what the model was given don't count.
    assert stored == []


def test_a_known_pattern_found_again_adds_to_its_count(monkeypatch, stored, redis):
    given(
        monkeypatch,
        flagged(3),
        [found(RULE, [1, 2])],
        [found("Something reworded", [1, 2, 3], same_as=1)],
        [found(RULE.upper().rstrip("."), [2, 3])],
    )

    for week in range(3):
        redis.counts.clear()
        asyncio.run(job.run())

    [row] = stored
    assert (row.text, row.question_count, row.seen_again) == (RULE, 7, 2)


def test_a_dismissed_pattern_is_never_proposed_again_or_counted(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(2), [found(RULE, [1, 2])], [found(RULE, [1, 2])])
    asyncio.run(job.run())
    stored[0].status = PatternStatus.DISMISSED
    redis.counts.clear()

    asyncio.run(job.run())

    [row] = stored
    assert (row.status, row.question_count, row.seen_again) == (PatternStatus.DISMISSED, 2, 0)
    # The model is told it's known, so it can point to it rather than reword it.
    assert f"Known patterns:\n1. {RULE}" in model.prompts[1]


@pytest.mark.parametrize(
    "text",
    [
        "Questions ask which of these keeps the ledger balanced.",
        "The scenario never says which Acme plan is meant.",
        "The code sample leaves out the version.",
        "x" * 301,
    ],
)
def test_a_pattern_failing_a_check_isnt_stored(monkeypatch, stored, redis, text):
    given(monkeypatch, [signal(), signal()], [found(text, [1, 2])])

    asyncio.run(job.run())

    assert stored == []


def test_only_the_rules_text_flag_count_and_status_are_stored(monkeypatch, redis):
    calls = []

    async def add(*args, **kwargs):
        calls.append((args, kwargs))

    async def none(flag):
        return []

    monkeypatch.setattr(storage, "add", add)
    monkeypatch.setattr(storage, "for_flag", none)
    given(monkeypatch, flagged(2), [found(RULE, [1, 2])])

    asyncio.run(job.run())

    # No question's id or text goes with it: the text, the flag and the count only.
    assert calls == [((RULE, "rewrite", 2), {})]


def test_a_flag_done_this_week_isnt_read_again(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(2), [found(RULE, [1, 2])], [found(RULE, [1, 2])])

    asyncio.run(job.run())
    asyncio.run(job.run())

    [row] = stored
    assert row.question_count == 2
    assert len(model.prompts) == 1
    assert PATTERN_DONE_KEY.format(flag="rewrite") in redis.counts


def test_a_flag_that_failed_isnt_marked_done(monkeypatch, stored, redis):
    given(monkeypatch, flagged(2), [found(RULE, [1, 2])])
    monkeypatch.setattr(job, "propose", fail)

    with pytest.raises(RuntimeError):
        asyncio.run(job.run())

    assert PATTERN_DONE_KEY.format(flag="rewrite") not in redis.counts
    # The lock is let go, so the next run isn't skipped.
    assert PATTERN_LOCK_KEY not in redis.counts


async def fail(flag, signals):
    raise RuntimeError("The model is down")


def test_a_run_still_going_skips_the_next(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(2), [found(RULE, [1, 2])])
    redis.counts[PATTERN_LOCK_KEY] = "another run"

    asyncio.run(job.run())

    assert (model.prompts, stored) == ([], [])


def test_the_emergency_pause_skips_the_job(monkeypatch, stored, redis):
    model = given(monkeypatch, flagged(2), [found(RULE, [1, 2])])

    async def on(redis):
        return True

    monkeypatch.setattr("prepza_common.pause.is_paused", on)

    asyncio.run(job.run())

    assert (model.prompts, stored) == ([], [])


def test_the_runs_ai_cost_is_recorded_under_its_own_line(monkeypatch, stored, redis, events):
    given(monkeypatch, flagged(2), [found(RULE, [1, 2])])

    asyncio.run(job.run())

    used = [data for kind, data in events if kind == AI_USED]
    assert [(data["action"], data["company_id"], data["user_id"]) for data in used] == [
        (QUALITY_PATTERNS, None, None)
    ]
    assert used[0]["outcome"] == "ok"
