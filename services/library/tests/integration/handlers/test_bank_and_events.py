import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events import processed_events
from sqlalchemy import text

from library.constants.sets import Pool
from library.core.db import Session
from library.handlers.dispatch import handle
from library.models.events import ProcessedEvent
from library.repositories import (
    accounts,
    answer_stats,
    feedback,
    preparations,
    quality,
    templates,
)
from tests.integration.factories import COPYABLE, a_company, direction, interview, set_pool


async def embedding_of(topic_id):
    async with Session() as session:
        return await session.scalar(
            text("SELECT embedding::text FROM topics WHERE id = :id"), {"id": topic_id}
        )


def test_an_answer_is_counted_once_however_often_its_event_arrives(run):
    async def scenario():
        template = await interview("Welder", template=True, questions=COPYABLE)
        copy = await templates.copy_template(template, a_company("11"))
        question = (await preparations.get_content(copy.id)).topics[0].questions[0]
        event_id = str(uuid.uuid4())
        first = await answer_stats.record_answer(
            event_id, question.id, question.text, ["right"], 1.0
        )
        again = await answer_stats.record_answer(
            event_id, question.id, question.text, ["right"], 1.0
        )
        _, copy_stats, *_ = await quality.load(question.id)
        _, original_stats, *_ = await quality.load(question.source_question_id)

        return first, again, question, copy_stats, original_stats

    first, again, question, copy_stats, original_stats = run(scenario())

    # The copy's answer counts for its bank original too.
    # How often each has been shown now.
    assert first == {question.id: 1, question.source_question_id: 1}
    assert again is None
    assert (copy_stats.answers, original_stats.answers) == (1, 1)


def test_a_scored_topic_is_counted_once_however_often_its_event_arrives(run):
    async def scenario():
        template = await interview("Plumber", template=True, questions=3)
        question = (await preparations.get_content(template)).topics[0].questions[0]
        result = {
            "question_id": str(question.id),
            "question_text": question.text,
            "correct": True,
            "timed_out": False,
        }
        event_id = str(uuid.uuid4())

        for _ in range(2):
            await handle(event_id, "session.scored", {"final_score": 90, "answers": [result]})

        _, stats, *_ = await quality.load(question.id)

        return stats

    stats = run(scenario())

    assert (stats.strong_answers, stats.strong_correct) == (1, 1)


def test_old_notes_of_processed_events_are_forgotten(run):
    async def scenario():
        template = await interview("Roofer", template=True, questions=3)
        question = (await preparations.get_content(template)).topics[0].questions[0]
        event_id = str(uuid.uuid4())
        await answer_stats.record_answer(event_id, question.id, question.text, ["right"], 1.0)
        forgotten = await processed_events.forget(
            Session, ProcessedEvent, datetime.now(UTC) + timedelta(seconds=1)
        )
        # Forgotten, it would count again: only events past Pub/Sub's redeliveries are dropped.
        again = await answer_stats.record_answer(
            event_id, question.id, question.text, ["right"], 1.0
        )

        return forgotten, again

    forgotten, again = run(scenario())

    assert forgotten >= 1
    assert again is not None


def test_a_copy_made_before_the_pools_of_a_now_practice_question_is_not_served(run):
    async def scenario():
        template = await interview("Baker", template=True, questions=COPYABLE)
        copy = await templates.copy_template(template, a_company("12"))
        copied = (await preparations.get_content(copy.id)).topics[0].questions
        # The migration put a question revealed after it was copied into practice.
        await set_pool([copied[0].source_question_id], Pool.PRACTICE)

        return (
            copied[0].id,
            [q.id for q in (await preparations.get_content(copy.id)).topics[0].questions],
            [count for _, count in await preparations.get_topics(copy.id)],
        )

    practice_copy, served, counts = run(scenario())

    assert practice_copy not in served
    assert len(served) == 9
    assert counts == [9]


def test_thin_template_topics_are_left_out_of_a_copy_which_keeps_their_embeddings(run):
    async def scenario():
        template = await interview(
            "Mason",
            template=True,
            questions=COPYABLE,
            topic_embeddings=[direction(1), direction(2)],
        )
        content = await preparations.get_content(template)
        # As an older template's topic can be, after the migration: with 4 company questions.
        company = [q.id for q in content.topics[1].questions if q.pool == Pool.COMPANY]
        await set_pool(company[:6], Pool.PRACTICE)
        copy = await templates.copy_template(template, a_company("13"))
        topics = await preparations.get_topics(copy.id)
        await set_pool(
            [q.id for q in content.topics[0].questions if q.pool == Pool.COMPANY], Pool.PRACTICE
        )
        nothing_left = await templates.copy_template(template, a_company("13"))

        return (
            [(topic.title, count) for topic, count in topics],
            copy.topic_count,
            await embedding_of(topics[0][0].id),
            await embedding_of(content.topics[0].id),
            nothing_left,
        )

    topics, topic_count, copied, original, nothing_left = run(scenario())

    # The second topic has 4 company questions, fewer than a candidate gets by default.
    assert topics == [("Python 0", 10)]
    assert topic_count == 1
    assert copied is not None and copied == original
    assert nothing_left is None


def test_a_user_reports_a_question_once_across_its_revisions(run):
    async def scenario():
        set_id = await interview("Reported", questions=1)
        question = (await preparations.get_content(set_id)).topics[0].questions[0]
        first = await feedback.report_question(question.id, "ann-r", "unclear", "")
        await preparations.replace_question(
            question.id, "A clearer question?", [{"answer": "Yes", "correct": True}]
        )
        again = await feedback.report_question(question.id, "ann-r", "unclear", "")
        reported = await feedback.has_reported(question.id, "ann-r")
        other = await feedback.report_question(question.id, "bob-r", "unclear", "")
        await accounts.delete_user("ann-r")
        after_deletion = await feedback.has_reported(question.id, "ann-r")

        return first, again, reported, other, after_deletion

    first, again, reported, other, after_deletion = run(scenario())

    assert (first, again, reported, other) == (True, False, True, True)
    assert after_deletion is False


def test_flags_left_unfixed_are_taken_for_sending_again_once_a_while(run):
    async def scenario():
        set_id = await interview("Flagged", questions=1)
        question = (await preparations.get_content(set_id)).topics[0].questions[0]
        await quality.save_flag(question.id, "rewrite")
        taken = await quality.take_stale_flags(datetime.now(UTC) + timedelta(seconds=1), 1000)
        # Dated now when taken, so an earlier cutoff doesn't take it again.
        again = await quality.take_stale_flags(datetime.now(UTC) - timedelta(hours=1), 1000)
        await quality.save_flag(question.id, None, kept=True)
        cleared = await quality.take_stale_flags(datetime.now(UTC) + timedelta(seconds=1), 1000)

        return question.id, taken, again, cleared

    question_id, taken, again, cleared = run(scenario())

    assert (question_id, "rewrite") in taken
    assert question_id not in [row[0] for row in again]
    assert question_id not in [row[0] for row in cleared]


def test_a_flag_another_sweep_holds_is_skipped_not_waited_for(run):
    async def scenario():
        set_id = await interview("Held", questions=1)
        question = (await preparations.get_content(set_id)).topics[0].questions[0]
        await quality.save_flag(question.id, "rewrite")

        # Another sweep holds the flag's row in its open transaction.
        async with Session() as other:
            await other.execute(
                text("SELECT 1 FROM question_stats WHERE question_id = :id FOR UPDATE"),
                {"id": question.id},
            )
            taken = await quality.take_stale_flags(datetime.now(UTC) + timedelta(seconds=1), 1000)
            await other.rollback()

        return question.id, taken

    question_id, taken = run(scenario())

    assert question_id not in [row[0] for row in taken]


def test_a_replaced_question_starts_its_own_statistics(run):
    """The old content's answers go into its revision; a late answer to the old text isn't
    counted for the new one."""

    async def scenario():
        set_id = await interview("Rewritten", questions=1)
        question = (await preparations.get_content(set_id)).topics[0].questions[0]
        await answer_stats.record_answer(str(uuid.uuid4()), question.id, question.text, ["a"], 1.0)
        await preparations.replace_question(
            question.id, "A clearer question?", [{"answer": "Yes", "correct": True}]
        )
        _, replaced, *_ = await quality.load(question.id)
        late = await answer_stats.record_answer(
            str(uuid.uuid4()), question.id, question.text, ["a"], 1.0
        )

        return replaced, late

    replaced, late = run(scenario())

    assert replaced is None
    assert late == {}
