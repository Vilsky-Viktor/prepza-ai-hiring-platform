import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from rounds.helpers.review import build_review
from rounds.helpers.sessions import answer_seconds
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.services import sections, session_answers

QUESTION_ID = uuid4()


def session(shown_at):
    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=uuid4(),
        topic_title="Python",
        status="in_progress",
        questions=[
            {
                "id": str(QUESTION_ID),
                "text": "Q?",
                "options": [
                    {"answer": "Right", "correct": True},
                    {"answer": "Wrong", "correct": False},
                ],
                "seconds": 49,
            }
        ],
        final_score=None,
        started_at=datetime.now(UTC),
        finished_at=None,
        question_seconds=60,
        question_shown_at=shown_at,
        answers=[],
    )


@pytest.fixture(autouse=True)
def finished(monkeypatch):
    """The sections the answers finish, by id."""
    rows = []

    async def fake_finish(session, session_id):
        rows.append(session_id)

    monkeypatch.setattr(sections, "finish", fake_finish)

    return rows


def test_answer_seconds():
    shown = datetime(2026, 10, 2, 12, 0, 0, tzinfo=UTC)

    assert answer_seconds(shown, shown + timedelta(seconds=12.4)) == 12
    assert answer_seconds(None, shown) is None


def test_answer_records_the_seconds_since_the_question_was_shown(monkeypatch):
    saved = []

    async def fake_add(session, answer, event=None):
        # As saving fills in the column defaults.
        answer.id, answer.timed_out = uuid4(), False
        saved.append(answer)

        return True

    async def no_flush():
        return None

    monkeypatch.setattr(sessions, "add_answer", fake_add)
    monkeypatch.setattr(session_answers.outbox_service, "flush_quietly", no_flush)
    row = session(datetime.now(UTC) - timedelta(seconds=30))

    asyncio.run(
        session_answers.submit_session_answer(
            row, AnswerCreate(question_id=QUESTION_ID, option_index=0)
        )
    )

    assert 29 <= saved[0].seconds <= 31
    row.answers = saved
    # The report shows it out of the question's own time.
    review = build_review(row)[0]
    assert (review.answer.seconds, review.limit_seconds) == (saved[0].seconds, 49)


def test_only_a_candidates_answer_tells_library_about_the_question(monkeypatch):
    events = []

    async def fake_add(session, answer, event=None):
        answer.id = uuid4()
        events.append(event)

        return True

    async def no_flush():
        return None

    monkeypatch.setattr(sessions, "add_answer", fake_add)
    monkeypatch.setattr(session_answers.outbox_service, "flush_quietly", no_flush)

    for preview in (False, True):
        row = session(datetime.now(UTC))
        row.preview = preview
        asyncio.run(
            session_answers.submit_session_answer(
                row, AnswerCreate(question_id=QUESTION_ID, option_index=0)
            )
        )

    # A company member trying their own test says nothing about the question's quality.
    assert events[0][0] == "answer.recorded"
    assert events[1] is None


def test_the_last_answer_finishes_the_section_at_once(monkeypatch, finished):
    async def fake_add(session, answer, event=None):
        answer.id = uuid4()

        return True

    async def no_flush():
        return None

    monkeypatch.setattr(sessions, "add_answer", fake_add)
    monkeypatch.setattr(session_answers.outbox_service, "flush_quietly", no_flush)
    last = session(datetime.now(UTC))
    first = session(datetime.now(UTC))
    first.questions = [*first.questions, {**first.questions[0], "id": str(uuid4())}]

    for row in (first, last):
        asyncio.run(
            session_answers.submit_session_answer(
                row, AnswerCreate(question_id=QUESTION_ID, option_index=0)
            )
        )

    # A question is still waiting in the first; the second has none left.
    assert finished == [last.id]
