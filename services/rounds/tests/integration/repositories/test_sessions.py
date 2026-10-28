import asyncio
import uuid

from rounds.models.answers import Answer
from rounds.repositories import practice_sessions, sessions, signals
from rounds.services import invite_scores, sections
from tests.integration.factories import MOST_SIGNALS, answered, created, option_index, topic
from tests.integration.transactions import transaction


def timed_out(session_id, question_id):
    return Answer(
        session_id=session_id,
        question_id=question_id,
        option_index=None,
        timed_out=True,
        correct=False,
        score=0,
        seconds=30,
    )


def test_two_requests_timing_out_the_same_question_save_one_answer(run):
    async def scenario():
        [row] = await created("cand", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())
        await transaction(sessions.mark_shown, row.id)
        question_id = uuid.UUID(row.questions[0]["id"])
        saved = await asyncio.gather(
            answered(timed_out(row.id, question_id)),
            answered(timed_out(row.id, question_id)),
        )

        return saved, await transaction(sessions.get, row.id)

    saved, row = run(scenario())

    assert sorted(saved) == [False, True]
    assert len(row.answers) == 1
    # The answer stopped the clock, so the next question starts its own.
    assert row.question_shown_at is None


def test_scores_show_progress_and_the_grade_of_answers_so_far(run):
    invite_id = uuid.uuid4()

    async def scenario():
        rows = await created("cand", invite_id, [topic(4)], 60, company_id=uuid.uuid4())
        row = rows[0]
        question = row.questions[0]
        correct = next(i for i, option in enumerate(question["options"]) if option["correct"])
        await transaction(
            sessions.add_answer,
            Answer(
                session_id=row.id,
                question_id=uuid.UUID(question["id"]),
                option_index=correct,
                correct=True,
                score=100,
            ),
        )

        return await invite_scores.scores([invite_id])

    totals = run(scenario())[invite_id]

    # One of four answered, and right: 25% through, 100% correct so far. Unanswered questions
    # count as wrong only in the final score, once the interview ends.
    assert (totals["progress"], totals["grade"], totals["finished"]) == (25, 100, False)
    assert (totals["tab_leaves"], totals["copies"], totals["fast_answers"]) == (0, 0, 0)


def test_a_finished_interview_grades_unanswered_questions_as_wrong(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created("cand", invite_id, [topic(4)], 60, company_id=uuid.uuid4())
        question = row.questions[0]
        correct = next(i for i, option in enumerate(question["options"]) if option["correct"])
        await transaction(
            sessions.add_answer,
            Answer(
                session_id=row.id,
                question_id=uuid.UUID(question["id"]),
                option_index=correct,
                correct=True,
                score=100,
            ),
        )
        await transaction(sections.finish, row.id)

        return await invite_scores.scores([invite_id])

    totals = run(scenario())[invite_id]

    # One right of four, the rest never answered: 25%, not the 100% of the answered one.
    assert (totals["grade"], totals["finished"]) == (25, True)


def test_a_talents_practice_rounds_on_a_template_are_found_and_kept_apart(run):
    user = f"talent-{uuid.uuid4()}"

    async def scenario():
        practice_topic = topic(2)
        first, second, third = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        for round_id in (first, second, third):
            await created(user, round_id, [practice_topic], 60, practice=True)

        # A company's interview on the same set isn't practice.
        await created(user, uuid.uuid4(), [practice_topic], 60, company_id=uuid.uuid4())
        template_id = practice_topic.preparation_id
        newest = await transaction(practice_sessions.practice_rounds, user, template_id, 0, 2)
        oldest = await transaction(practice_sessions.practice_rounds, user, template_id, 2, 2)
        before = await transaction(practice_sessions.practiced, user, template_id)
        never = await transaction(practice_sessions.practiced, f"other-{user}", template_id)

        return (first, second, third), newest, oldest, before, never

    (first, second, third), newest, oldest, before, never = run(scenario())

    assert (before, never) == (True, False)
    # A page of rounds, newest first, with every section of each.
    assert {row.candidate_invite_id for row in newest} == {second, third}
    assert {row.candidate_invite_id for row in oldest} == {first}
    assert all(row.practice for row in newest + oldest)


def test_a_finished_section_takes_no_more_answers_and_is_scored_from_its_saved_ones(run):
    async def scenario():
        [row] = await created("cand", uuid.uuid4(), [topic(4)], 60, company_id=uuid.uuid4())
        first, second = (uuid.UUID(question["id"]) for question in row.questions[:2])
        right = Answer(
            session_id=row.id,
            question_id=first,
            option_index=option_index(row.questions[0], True),
            correct=True,
            score=100,
        )
        await transaction(sessions.add_answer, right)
        await transaction(sections.finish, row.id)
        late = await transaction(sessions.add_answer, timed_out(row.id, second))

        return late, await transaction(sessions.get, row.id)

    late, row = run(scenario())

    assert late is False
    assert len(row.answers) == 1
    # One right of four.
    assert row.final_score == 25


def test_timed_out_questions_count_in_progress_but_not_as_picked_answers(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created("cand", invite_id, [topic(4)], 60, company_id=uuid.uuid4())
        first, second = (uuid.UUID(question["id"]) for question in row.questions[:2])
        await transaction(sessions.add_answer, timed_out(row.id, first))
        await transaction(sessions.add_answer, timed_out(row.id, second))

        return await invite_scores.scores([invite_id])

    totals = run(scenario())[invite_id]

    # Two of four ran out: half way through, yet nothing picked, so nothing to charge for.
    assert (totals["progress"], totals["picked"]) == (50, 0)


def test_two_tabs_starting_the_clock_get_the_same_time(run):
    async def scenario():
        [row] = await created("cand", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())

        return await asyncio.gather(
            transaction(sessions.mark_shown, row.id), transaction(sessions.mark_shown, row.id)
        )

    first, second = run(scenario())

    assert first == second


def test_scores_add_up_every_section_its_signals_and_fast_answers(run):
    invite_id = uuid.uuid4()
    other_id = uuid.uuid4()

    async def scenario():
        rows = await created("cand", invite_id, [topic(2), topic(2)], 60, company_id=uuid.uuid4())
        await created("cand", other_id, [topic(2)], 60, company_id=uuid.uuid4())

        for row, (score, seconds) in zip(rows, [(100, 1), (0, 20)]):
            await transaction(
                sessions.add_answer,
                Answer(
                    session_id=row.id,
                    question_id=uuid.UUID(row.questions[0]["id"]),
                    option_index=option_index(row.questions[0], bool(score)),
                    correct=bool(score),
                    score=score,
                    seconds=seconds,
                ),
            )

        await transaction(signals.add_signal, rows[0].id, None, "tab_leave", MOST_SIGNALS)
        await transaction(signals.add_signal, rows[1].id, None, "tab_leave", MOST_SIGNALS)
        await transaction(signals.add_signal, rows[1].id, None, "copy", MOST_SIGNALS)

        return await invite_scores.scores([invite_id, other_id])

    found = run(scenario())

    # Two of four answered, one right; the right one was picked in a second, too fast.
    assert found[invite_id] == {
        "progress": 50,
        "grade": 50,
        "finished": False,
        "tab_leaves": 2,
        "copies": 1,
        "fast_answers": 1,
        "picked": 2,
    }
    assert found[other_id] == {
        "progress": 0,
        "grade": None,
        "finished": False,
        "tab_leaves": 0,
        "copies": 0,
        "fast_answers": 0,
        "picked": 0,
    }


def test_sections_keep_their_topics_order(run):
    async def scenario():
        invite_id = uuid.uuid4()
        topics = [topic(size=1) for _ in range(5)]
        await created("cand", invite_id, topics, 60, company_id=uuid.uuid4())
        listed = await transaction(sessions.list_for_invite, invite_id)

        return [row.topic_id for row in listed], [item.id for item in topics]

    listed, topics = run(scenario())

    assert listed == topics
