import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from rounds.constants.rounds import TIME_UP
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.services import sections, session_answers

QUESTION_ID = uuid4()
# Three right options of four: B, C and D.
MULTI = [
    {"answer": "A", "correct": False},
    {"answer": "B", "correct": True},
    {"answer": "C", "correct": True},
    {"answer": "D", "correct": True},
]
SINGLE = [{"answer": "A", "correct": True}, {"answer": "B", "correct": False}]


def section(options, answers=None):
    """A section of one question, on screen since a few seconds ago."""
    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=uuid4(),
        topic_title="Ledgers",
        status="in_progress",
        questions=[{"id": str(QUESTION_ID), "text": "Which are assets?", "options": options}],
        final_score=None,
        started_at=datetime.now(UTC),
        finished_at=None,
        question_seconds=None,
        question_shown_at=datetime.now(UTC) - timedelta(seconds=5),
        answers=answers or [],
    )


@pytest.fixture
def saved(monkeypatch):
    """Every answer saved, with the event saved alongside it."""
    rows = []

    async def fake_add(session, answer, event=None):
        answer.id = uuid4()
        rows.append((answer, event))

        return True

    async def nothing(*args):
        return None

    monkeypatch.setattr(sessions, "add_answer", fake_add)
    monkeypatch.setattr(sections, "finish", nothing)
    monkeypatch.setattr(session_answers.outbox_service, "flush_quietly", nothing)

    return rows


def submit(row, **answer):
    return asyncio.run(
        session_answers.submit_session_answer(row, AnswerCreate(question_id=QUESTION_ID, **answer))
    )


def refusal(row, **answer):
    with pytest.raises(HTTPException) as error:
        submit(row, **answer)

    return error.value.status_code, error.value.detail


@pytest.mark.parametrize(
    ("picks", "score", "correct", "credit"),
    [
        ([1, 2, 3], 100, True, 1.0),
        ([3, 1], 67, False, 0.67),
        ([1, 2, 0], 0, False, 0.0),
    ],
)
def test_ticks_on_a_multi_answer_question_are_saved_and_scored(
    saved, picks, score, correct, credit
):
    submit(section(MULTI), picks=picks)
    [(answer, (event_type, event))] = saved

    assert (answer.option_index, answer.picks) == (None, sorted(picks))
    assert (answer.score, answer.correct) == (score, correct)
    # Library counts each option ticked, and the credit earned.
    assert event_type == "answer.recorded"
    assert event["options"] == [MULTI[index]["answer"] for index in sorted(picks)]
    assert event["option"] == event["options"][0]
    assert (event["correct"], event["credit"]) == (correct, credit)


def test_a_single_answer_question_takes_one_pick_sent_either_way(saved):
    submit(section(SINGLE), option_index=0)
    submit(section(SINGLE), picks=[1])
    [(right, right_event), (wrong, wrong_event)] = saved

    assert [(a.option_index, a.picks, a.score) for a in (right, wrong)] == [
        (0, None, 100),
        (1, None, 0),
    ]
    assert [(event[1]["options"], event[1]["credit"]) for event in (right_event, wrong_event)] == [
        (["A"], 1.0),
        (["B"], 0.0),
    ]


def test_several_picks_on_a_single_answer_question_are_refused(saved):
    assert refusal(section(SINGLE), picks=[0, 1]) == (422, "Pick one option for this question.")
    assert saved == []


def test_the_same_ticks_sent_again_are_answered_as_before_and_other_ticks_refused(saved):
    answer = Answer(id=uuid4(), question_id=QUESTION_ID, picks=[1, 3], correct=False, score=67)
    row = section(MULTI, answers=[answer])
    row.status = "finished"

    # In any order: the same options.
    result = submit(row, picks=[3, 1])

    assert (result.answer_id, result.answered) == (answer.id, 1)
    assert refusal(row, picks=[1, 2, 3])[0] == 409
    assert saved == []


def test_a_multi_answer_answer_is_not_mistaken_for_a_timed_out_one(saved):
    """Both leave option_index empty; only a timed-out one refuses with time up."""
    ticked = Answer(
        id=uuid4(), question_id=QUESTION_ID, picks=[1, 2], timed_out=False, correct=False, score=67
    )
    ran_out = Answer(id=uuid4(), question_id=QUESTION_ID, timed_out=True, correct=False, score=0)

    assert refusal(section(MULTI, answers=[ticked]), picks=[1]) != (409, TIME_UP)
    assert refusal(section(MULTI, answers=[ran_out]), picks=[1]) == (409, TIME_UP)
