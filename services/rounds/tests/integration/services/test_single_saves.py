"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the candidate's next step finds the action whole still to
do."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from prepza_common.auth.user import User
from sqlalchemy import update

from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session
from rounds.models.answers import Answer
from rounds.models.sessions import Session as SessionRow
from rounds.repositories import sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.services import interview_flow, sections, session_expiry
from rounds.services import outbox as outbox_service
from rounds.services.session_access import get_owned_session
from rounds.services.session_answers import submit_session_answer
from tests.integration.factories import created, option_index, topic
from tests.integration.transactions import transaction

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)


async def broken(*args):
    raise RuntimeError("The database went away")


def broken_after(monkeypatch, calls: int):
    """`sections.finish` works `calls` times, then fails."""
    real = sections.finish
    done = []

    async def finish(session, section_id):
        if len(done) == calls:
            raise RuntimeError("The database went away")

        done.append(section_id)
        await real(session, section_id)

    monkeypatch.setattr(sections, "finish", finish)


@pytest.fixture(autouse=True)
def unsent(monkeypatch):
    """The outbox isn't sent: what each action wrote stays to be read."""

    async def nothing():
        pass

    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)


async def interview(sizes: list[int]) -> list[SessionRow]:
    """A candidate's interview, a section a size, the first one's question on screen."""
    rows = await created(
        "cand", uuid.uuid4(), [topic(size) for size in sizes], 30, company_id=uuid.uuid4()
    )
    await transaction(sessions.mark_shown, rows[0].id)

    return rows


async def shown_ago(row_id, seconds: int) -> None:
    async with Session.begin() as session:
        shown = datetime.now(UTC) - timedelta(seconds=seconds)
        await session.execute(
            update(SessionRow).where(SessionRow.id == row_id).values(question_shown_at=shown)
        )


def test_the_last_answer_isnt_kept_without_the_finish_it_brings(run, monkeypatch):
    monkeypatch.setattr(sections, "finish", broken)

    async def scenario():
        [row] = await interview([1])
        loaded = await transaction(sessions.get, row.id)
        question = loaded.questions[0]
        body = AnswerCreate(
            question_id=uuid.UUID(question["id"]), option_index=option_index(question, True)
        )

        with pytest.raises(RuntimeError):
            await submit_session_answer(loaded, body)

        return await transaction(sessions.get, row.id)

    assert run(scenario()).answers == []


def test_a_last_question_timing_out_isnt_kept_without_the_finish_it_brings(run, monkeypatch):
    monkeypatch.setattr(sections, "finish", broken)

    async def scenario():
        [row] = await interview([1])
        await shown_ago(row.id, 60)

        with pytest.raises(RuntimeError):
            await get_owned_session(row.id, CANDIDATE)

        return await transaction(sessions.get, row.id)

    assert run(scenario()).answers == []


def test_a_finished_section_isnt_kept_without_the_next_questions_clock(run, monkeypatch):
    monkeypatch.setattr(sessions, "mark_shown", broken)

    async def scenario():
        done, _ = await created(
            "cand", uuid.uuid4(), [topic(1), topic(1)], 30, company_id=uuid.uuid4()
        )
        question = done.questions[0]
        # The section's only answer is saved without finishing it, as before the step.
        right = Answer(
            session_id=done.id,
            question_id=uuid.UUID(question["id"]),
            option_index=option_index(question, True),
            correct=True,
            score=100,
        )
        await transaction(sessions.add_answer, right)

        with pytest.raises(RuntimeError):
            await interview_flow.interview_step(await transaction(sessions.get, done.id), CANDIDATE)

        return await transaction(sessions.get, done.id)

    assert run(scenario()).status == RoundStatus.IN_PROGRESS


@pytest.mark.parametrize("action", ["expiry", "candidate"])
def test_ending_an_interview_finishes_every_section_or_none(run, monkeypatch, action):
    """The interview's time ran out, or the candidate ends it: its open sections finish
    together."""
    broken_after(monkeypatch, 1)

    async def scenario():
        rows = await interview([2, 2])

        with pytest.raises(RuntimeError):
            if action == "expiry":
                await session_expiry.finish_invite(rows[0].candidate_invite_id)
            else:
                await interview_flow.finish_interview(rows[0], CANDIDATE)

        return [await transaction(sessions.get, row.id) for row in rows]

    assert [row.status for row in run(scenario())] == [RoundStatus.IN_PROGRESS] * 2
