import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User
from prepza_common.http.http import bearer

from rounds.constants.rounds import TIME_UP
from rounds.core.security import service_token
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import session_expiry, sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.services import outbox as outbox_service
from rounds.services.session_access import get_owned_session
from rounds.services.session_answers import submit_session_answer

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)
INVITE_ID = uuid4()
QUESTION_ID = uuid4()


def timed(shown_seconds_ago, answers=None):
    """A section whose question has 30 seconds and was shown this many seconds ago."""
    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=INVITE_ID,
        topic_title="Python",
        status="in_progress",
        questions=[
            {
                "id": str(QUESTION_ID),
                "text": "Q?",
                "options": [{"answer": "A", "correct": True}, {"answer": "B", "correct": False}],
            }
        ],
        final_score=None,
        started_at=datetime.now(UTC),
        finished_at=None,
        question_seconds=30,
        question_shown_at=datetime.now(UTC) - timedelta(seconds=shown_seconds_ago),
        answers=answers or [],
    )


def test_starting_a_timed_interview_passes_the_seconds_per_question(client, monkeypatch):
    created = {}

    async def no_sessions(invite_id):
        return []

    async def fake_create(user_id, invite_id, topics, question_seconds, preview, company_id=None):
        created["question_seconds"] = question_seconds
        created["preview"] = preview

        return []

    monkeypatch.setattr(sessions, "list_for_invite", no_sessions)
    monkeypatch.setattr(sessions, "create_many", fake_create)
    body = {
        "user_id": "cand",
        "company_id": str(uuid4()),
        "candidate_invite_id": str(INVITE_ID),
        "topics": [],
        "question_seconds": 45,
    }

    response = client.post(
        "/internal/sessions",
        json=body,
        headers=bearer(service_token("rounds")),
    )

    assert response.status_code == 201
    assert created["question_seconds"] == 45
    assert created["preview"] is False


def test_a_question_past_its_time_counts_as_wrong(monkeypatch):
    expired = timed(shown_seconds_ago=40)
    saved = []

    async def fake_get(session_id):
        return expired

    async def fake_add(answer):
        saved.append(answer)
        expired.answers = [answer]

        return True

    async def fake_finish(session_id):
        finished.append(session_id)

    async def no_flush():
        return None

    finished = []
    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(sessions, "add_answer", fake_add)
    monkeypatch.setattr(sessions, "finish", fake_finish)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)

    asyncio.run(get_owned_session(expired.id, CANDIDATE))

    assert [(a.question_id, a.option_index, a.correct, a.score) for a in saved] == [
        (QUESTION_ID, None, False, 0)
    ]
    # It was the section's last question: the section finishes at once.
    assert finished == [expired.id]


def test_a_question_within_its_time_is_left_alone(monkeypatch):
    running = timed(shown_seconds_ago=10)

    async def fake_get(session_id):
        return running

    async def never(answer):
        raise AssertionError("must not time out a running question")

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(sessions, "add_answer", never)

    assert asyncio.run(get_owned_session(running.id, CANDIDATE)).answers == []


def test_no_answer_once_the_question_timed_out():
    timed_out = Answer(
        question_id=QUESTION_ID, option_index=None, timed_out=True, correct=False, score=0
    )
    row = timed(shown_seconds_ago=40, answers=[timed_out])

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            submit_session_answer(row, AnswerCreate(question_id=QUESTION_ID, option_index=0))
        )

    assert error.value.status_code == 409
    assert error.value.detail == TIME_UP


def test_the_same_pick_sent_again_is_answered_as_before_and_another_is_refused():
    """Its reply lost on the way, the candidate sends the answer again: even once it finished the
    section, it's the answer already saved, not a refusal that looks like a lost answer."""
    saved = Answer(id=uuid4(), question_id=QUESTION_ID, option_index=2, correct=True, score=1)
    row = timed(shown_seconds_ago=5, answers=[saved])
    row.status = "finished"
    again = AnswerCreate(question_id=QUESTION_ID, option_index=2)

    result = asyncio.run(submit_session_answer(row, again))

    assert (result.answer_id, result.answered) == (saved.id, 1)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            submit_session_answer(row, AnswerCreate(question_id=QUESTION_ID, option_index=1))
        )

    assert error.value.status_code == 409


def test_only_the_question_on_screen_can_be_answered():
    row = timed(shown_seconds_ago=5)
    row.question_shown_at = None

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            submit_session_answer(row, AnswerCreate(question_id=QUESTION_ID, option_index=0))
        )

    assert error.value.status_code == 409


def test_coming_back_after_the_interview_ran_out_finishes_it(monkeypatch):
    row = timed(shown_seconds_ago=5)
    finished = []

    async def fake_get(session_id):
        return row

    async def expired(now, limit, invite_id=None):
        return [invite_id]

    async def fake_list(invite_id):
        return [row]

    async def fake_finish(session_id):
        finished.append(session_id)
        row.status = "finished"

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(session_expiry, "expired_invites", expired)
    monkeypatch.setattr(sessions, "list_for_invite", fake_list)
    monkeypatch.setattr(sessions, "finish", fake_finish)

    assert asyncio.run(get_owned_session(row.id, CANDIDATE)).status == "finished"
    assert finished == [row.id]
