import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from library.constants.quality import MIN_ANSWERS, QualityFlag
from library.core.db import Session
from library.handlers.dispatch import handle
from library.integrations import generation
from library.models.quality import QuestionStats
from library.repositories import answer_stats, preparations, quality
from library.services import questions as question_service
from tests.integration.factories import interview
from tests.integration.transactions import transaction

# Two right options of four.
MULTI = [
    {"answer": "Cash", "correct": True},
    {"answer": "Bank", "correct": True},
    {"answer": "Revenue", "correct": False},
    {"answer": "Expenses", "correct": False},
]


async def multi_question(title):
    """A company test's one question, made multi-answer."""
    set_id = await interview(title, questions=1)
    question = (await transaction(preparations.get_content, set_id)).topics[0].questions[0]
    await question_service.replace(question.id, f"{title}: which are assets?", MULTI)

    return (await transaction(preparations.get_content, set_id)).topics[0].questions[0]


def test_an_answer_counts_a_pick_for_every_option_ticked_and_its_credit(run):
    async def scenario():
        question = await multi_question("Ledger picks")

        for options, credit in ((["Cash", "Bank"], 1.0), (["Cash"], 0.5), (["Cash", "Revenue"], 0)):
            await transaction(
                answer_stats.record_answer,
                str(uuid.uuid4()),
                question.id,
                question.text,
                options,
                credit,
            )

        _, stats, *_ = await transaction(quality.load, question.id)

        return stats

    stats = run(scenario())

    assert (stats.answers, stats.correct) == (3, 1.5)
    assert stats.option_picks == {"Cash": 3, "Bank": 1, "Revenue": 1}


def test_answer_events_old_and_new_add_up_in_the_statistics(run):
    async def scenario():
        question = await multi_question("Ledger events")
        base = {"question_id": str(question.id), "question_text": question.text}
        partly = base | {"option": "Cash", "options": ["Cash"], "correct": False, "credit": 0.5}
        # From before multi-answer questions: one option, no credit.
        old = base | {"option": "Bank", "correct": True}

        for event in (partly, old):
            await handle(str(uuid.uuid4()), "answer.recorded", event)

        _, stats, *_ = await transaction(quality.load, question.id)

        return stats

    stats = run(scenario())

    assert (stats.answers, stats.correct) == (2, 1.5)
    assert stats.option_picks == {"Cash": 1, "Bank": 1}


def test_a_scored_topic_counts_each_answers_credit_in_its_group(run):
    async def scenario():
        question = await multi_question("Ledger groups")
        result = {"question_id": str(question.id), "question_text": question.text}
        strong = result | {"correct": False, "credit": 0.5, "timed_out": False}
        # From before multi-answer questions: no credit.
        weak = result | {"correct": True, "timed_out": False}
        await handle(str(uuid.uuid4()), "session.scored", {"final_score": 90, "answers": [strong]})
        await handle(str(uuid.uuid4()), "session.scored", {"final_score": 20, "answers": [weak]})
        _, stats, *_ = await transaction(quality.load, question.id)

        return stats

    stats = run(scenario())

    assert (stats.strong_answers, stats.strong_correct) == (1, 0.5)
    assert (stats.weak_answers, stats.weak_correct) == (1, 1.0)


def test_a_wrong_option_ticked_more_than_a_right_one_flags_a_multi_answer_key(run, monkeypatch):
    sent = []

    async def verify_question(question_id, flag):
        sent.append(flag)

    monkeypatch.setattr(generation, "verify_question", verify_question)

    async def scenario():
        question = await multi_question("Ledger key")
        ticked = {
            "question_id": str(question.id),
            "question_text": question.text,
            "option": "Cash",
            "options": ["Cash", "Revenue"],
            "correct": False,
            "credit": 0.0,
        }

        # Every candidate ticks a right option and a wrong one; no one the other right one.
        for _ in range(MIN_ANSWERS):
            await handle(str(uuid.uuid4()), "answer.recorded", ticked)

        _, stats, *_ = await transaction(quality.load, question.id)

        return stats.flag

    assert run(scenario()) == QualityFlag.WRONG_KEY
    assert sent == [QualityFlag.WRONG_KEY]


@pytest.mark.parametrize("column", ["correct", "strong_correct", "weak_correct"])
def test_the_credit_migration_keeps_counts_and_takes_fractions(run, column):
    async def setup():
        question = await multi_question(f"Ledger migration {column}")

        async with Session() as session:
            session.add(QuestionStats(question_id=question.id, answers=3, **{column: 2}))
            await session.commit()

        return question

    async def stored(question_id):
        async with Session() as session:
            return await session.scalar(
                text(f"SELECT {column} FROM question_stats WHERE question_id = :id"),
                {"id": question_id},
            )

    question = run(setup())
    config = Config("alembic.ini")
    command.downgrade(config, "0027")
    command.upgrade(config, "head")
    kept = run(stored(question.id))
    run(
        transaction(
            answer_stats.record_answer, str(uuid.uuid4()), question.id, question.text, ["Cash"], 0.5
        )
    )

    assert kept == 2
    assert run(stored(question.id)) == (2.5 if column == "correct" else 2)


def test_a_replaced_multi_answer_question_keeps_its_credit_in_its_revision(run):
    async def scenario():
        question = await multi_question("Ledger revision")
        await transaction(
            answer_stats.record_answer, str(uuid.uuid4()), question.id, question.text, ["Cash"], 0.5
        )
        await question_service.replace(question.id, "Which are liabilities?", MULTI)

        async with Session() as session:
            return await session.scalar(
                text(
                    "SELECT correct FROM question_revisions WHERE question_id = :id "
                    "ORDER BY replaced_at DESC LIMIT 1"
                ),
                {"id": question.id},
            )

    assert run(scenario()) == 0.5
