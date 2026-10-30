"""Voice mode's last moment: a spoken answer the service received by its question's deadline
(plus the upload's margin) counts when its result comes a little later, through the answers
route as a tap would; anything later is refused as late, and only one answer is ever saved."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User
from prepza_common.db.lock_waits import hold_first_commit, race
from sqlalchemy import update

from rounds.api.v1.sessions import answer_question
from rounds.constants.rounds import TIME_UP
from rounds.constants.voice import VOICE_ANSWER_GRACE_SECONDS, VOICE_UPLOAD_SECONDS
from rounds.core.db import Session
from rounds.models.sessions import Session as SessionRow
from rounds.repositories import sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.services import outbox as outbox_service
from rounds.services import session_answers, voice_deadline
from rounds.services.session_access import time_out
from tests.integration.factories import created, option_index, topic
from tests.integration.transactions import transaction

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)
SECONDS = 30


@pytest.fixture(autouse=True)
def unsent(monkeypatch):
    """The outbox isn't sent: nothing reads it here."""

    async def nothing():
        pass

    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)


async def shown_ago(row_id, seconds: float) -> None:
    async with Session.begin() as session:
        shown = datetime.now(UTC) - timedelta(seconds=seconds)
        await session.execute(
            update(SessionRow).where(SessionRow.id == row_id).values(question_shown_at=shown)
        )


async def heard(arrived: float, answered: float):
    """A section of two questions of SECONDS each: a spoken answer reaches the service `arrived`
    seconds after the first question's deadline, and its result is sent `answered` seconds after
    it. The section and the first question's answer."""
    [row] = await created("cand", uuid.uuid4(), [topic(2)], SECONDS, company_id=uuid.uuid4())
    await transaction(sessions.mark_shown, row.id)
    await shown_ago(row.id, SECONDS + arrived)
    loaded = await transaction(sessions.get, row.id)
    question = loaded.questions[0]
    await voice_deadline.note_arrival(loaded, uuid.UUID(question["id"]))
    await shown_ago(row.id, SECONDS + answered)
    body = AnswerCreate(question_id=question["id"], option_index=option_index(question, True))

    return row, body


async def saved_answers(row_id):
    return (await transaction(sessions.get, row_id)).answers


def test_an_answer_heard_in_time_counts_after_the_deadline(run):
    async def scenario():
        row, body = await heard(VOICE_UPLOAD_SECONDS - 1, VOICE_ANSWER_GRACE_SECONDS - 3)
        result = await answer_question(row.id, body, CANDIDATE)

        return result, await saved_answers(row.id)

    result, answers = run(scenario())

    assert result.answered == 1
    [answer] = answers
    assert answer.correct and not answer.timed_out


@pytest.mark.parametrize(
    ("arrived", "answered"),
    [
        # Reached the service after the upload's margin.
        (VOICE_UPLOAD_SECONDS + 1, VOICE_UPLOAD_SECONDS + 7),
        # In time, but its result came after the grace.
        (0, VOICE_ANSWER_GRACE_SECONDS + 2),
    ],
)
def test_a_late_spoken_answer_is_refused_and_the_question_times_out(run, arrived, answered):
    async def scenario():
        row, body = await heard(arrived, answered)

        with pytest.raises(HTTPException) as refused:
            await answer_question(row.id, body, CANDIDATE)

        return refused.value, await saved_answers(row.id)

    refused, answers = run(scenario())

    assert (refused.status_code, refused.detail) == (409, TIME_UP)
    [answer] = answers
    assert answer.timed_out


def test_an_answer_heard_in_time_and_a_time_out_at_once_save_one_answer(run, monkeypatch):
    """The spoken answer's result is saving when another request times the question out (a
    second tab's step): the time-out waits on the section's lock, then finds the question
    answered, and only the answer is kept."""

    async def scenario():
        row, body = await heard(0, VOICE_ANSWER_GRACE_SECONDS - 5)
        loaded = await transaction(sessions.get, row.id)
        held = hold_first_commit(monkeypatch, session_answers, "Db")
        outcomes = await race(
            os.environ["DATABASE_URL"],
            held,
            answer_question(row.id, body, CANDIDATE),
            time_out(loaded),
        )

        return outcomes, await saved_answers(row.id)

    (result, timed_out), answers = run(scenario())

    assert result.answered == 1
    assert timed_out is False
    [answer] = answers
    assert answer.correct and not answer.timed_out
