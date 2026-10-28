"""What the weekly pattern job's model reads (services/patterns.py): its role and task apart,
the questions as tagged data, at most a flag's limit of them."""

import asyncio

from generation.constants.patterns import MAX_PATTERN_QUESTIONS
from generation.services import patterns as job
from tests.unit.services.test_pattern_job import (  # noqa: F401
    RULE,
    flagged,
    found,
    given,
    redis,
    stored,
)


def test_the_model_reads_at_most_the_limit_of_one_flags_questions(monkeypatch, stored, redis):  # noqa: F811 - the fixtures imported above
    model = given(monkeypatch, flagged(MAX_PATTERN_QUESTIONS + 5), [found(RULE, [1, 61, 62])])

    asyncio.run(job.run())

    assert (
        f"{MAX_PATTERN_QUESTIONS}. Question number {MAX_PATTERN_QUESTIONS - 1}?"
        in (model.prompts[0])
    )
    assert f"Question number {MAX_PATTERN_QUESTIONS}?" not in model.prompts[0]
    # Numbers past what the model was given don't count.
    assert stored == []


def test_the_questions_are_data_in_the_users_message_after_the_role(monkeypatch, stored, redis):  # noqa: F811 - the fixtures imported above
    asked = []
    model = given(monkeypatch, flagged(2), [found(RULE, [1, 2])])
    ainvoke = model.ainvoke

    async def recorded(messages):
        asked.extend(messages)

        return await ainvoke(messages)

    monkeypatch.setattr(model, "ainvoke", recorded)

    asyncio.run(job.run())

    system, user = asked
    assert system.type == "system" and system.content.startswith("You are")
    assert "Question number" not in system.content
    assert "<questions>\n1. Question number 0?" in user.content
