"""What generation's weekly pattern job reads (/internal/questions/signals), against the real
database: last week's flagged and replaced questions with what showed they were bad, and nothing
that tells whose they are."""

import uuid

from sqlalchemy import update

from library.core.db import Session
from library.models.quality import QuestionRevision
from library.repositories import answer_stats, feedback, preparations, quality
from library.services import quality_signals
from tests.integration.factories import interview

COMMENT = "Private note from a candidate"
# The company that owns these tests (sets.owner_id holds a company's uuid).
OWNER = str(uuid.uuid4())


async def questions(title, count):
    """A company's test of its own (its owner unique), and its questions; each question's text
    starts with the test's title."""
    created = await interview(title, owner=OWNER, questions=count)

    return created, (await preparations.get_content(created)).topics[0].questions


async def reported(question_id, reason, times=2):
    for _ in range(times):
        await feedback.report_question(question_id, f"user-{uuid.uuid4()}", reason, COMMENT)


def mine(signals, *texts):
    return {signal.text: signal for signal in signals if signal.text in texts}


def test_a_flagged_question_comes_with_its_flag_answers_and_feedback(run):
    title = f"Signals {uuid.uuid4()}"

    async def scenario():
        set_id, [question, _] = await questions(title, 2)
        await answer_stats.record_answer(
            str(uuid.uuid4()), question.id, question.text, ["wrong"], 0.0
        )
        await reported(question.id, "wrong_answer")
        await feedback.rate_question(question.id, "user-1", -1)
        await quality.save_flag(question.id, "wrong_key")

        return set_id, question, await quality_signals.recent(7)

    set_id, question, signals = run(scenario())

    found = mine(signals, question.text)[question.text]
    assert (found.flag, found.answers, found.correct, found.option_picks) == (
        "wrong_key",
        1,
        0.0,
        {"wrong": 1},
    )
    assert (found.reasons, found.likes, found.dislikes) == ({"wrong_answer": 2}, 0, 1)
    # Nothing that tells whose it is: no id, set, owner or report comment.
    sent = found.model_dump_json()

    for kept_back in (str(question.id), str(set_id), OWNER, COMMENT):
        assert kept_back not in sent

    assert sent.count(title) == 1

    # A question with nothing wrong isn't sent.
    assert len([signal for signal in signals if signal.text.startswith(title)]) == 1


def test_a_replaced_question_comes_with_the_flag_it_had_and_what_replaced_it(run):
    title = f"Replaced {uuid.uuid4()}"

    async def scenario():
        _, [flagged, edited] = await questions(title, 2)
        await reported(flagged.id, "unclear")
        await quality.save_flag(flagged.id, "rewrite")
        await preparations.replace_question(
            flagged.id, f"{title} clearer?", [{"answer": "Yes", "correct": True}]
        )
        # An owner's edit of a question nothing was wrong with.
        await preparations.replace_question(
            edited.id, f"{title} edited?", [{"answer": "Yes", "correct": True}]
        )

        return flagged, edited, await quality_signals.recent(7)

    flagged, edited, signals = run(scenario())

    found = mine(signals, flagged.text, edited.text)
    assert list(found) == [flagged.text]
    replaced = found[flagged.text]
    assert (replaced.flag, replaced.reasons, replaced.new_text) == (
        "rewrite",
        {"unclear": 2},
        f"{title} clearer?",
    )
    assert [option.answer for option in replaced.new_options] == ["Yes"]
    assert COMMENT not in replaced.model_dump_json()


def test_a_revision_kept_before_flags_were_kept_gets_the_flag_its_feedback_gives(run):
    title = f"Old revision {uuid.uuid4()}"

    async def scenario():
        _, [question] = await questions(title, 1)
        await reported(question.id, "off_topic")
        await preparations.replace_question(
            question.id, f"{title} new?", [{"answer": "Yes", "correct": True}]
        )

        # As the migration leaves revisions kept before it: no flag.
        async with Session() as session:
            await session.execute(
                update(QuestionRevision)
                .where(QuestionRevision.question_id == question.id)
                .values(flag=None)
            )
            await session.commit()

        return question, await quality_signals.recent(7)

    question, signals = run(scenario())

    assert mine(signals, question.text)[question.text].flag == "rewrite"
