import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User

from rounds.integrations import library
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.services import interview_flow, sections, voice_session

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)
INVITE_ID = uuid4()


def section(answered=False, status="in_progress"):
    """A section with one question, answered or not."""
    question_id = uuid4()

    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=INVITE_ID,
        topic_title="Python",
        status=status,
        questions=[
            {
                "id": str(question_id),
                "text": "Q?",
                "options": [{"answer": "A", "correct": True}],
                "seconds": 30,
            }
        ],
        final_score=None,
        started_at=datetime.now(UTC),
        finished_at=None,
        question_seconds=30,
        question_shown_at=None,
        answers=[Answer(question_id=question_id, option_index=0, score=100)] if answered else [],
    )


@pytest.fixture
def interview(monkeypatch):
    """Fakes the repositories of one candidate's interview made of the sections a test passes."""
    rows = []
    finished = []

    async def fake_get(session, session_id):
        return next(row for row in rows if row.id == session_id)

    async def fake_list(session, invite_id):
        return rows

    async def fake_finish(session, session_id):
        finished.append(session_id)
        (await fake_get(session, session_id)).status = "finished"

    async def fake_shown(session, session_id, reading=None):
        return datetime.now(UTC), reading

    async def no_library(set_id):
        return None

    async def nothing():
        return None

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(sessions, "list_for_invite", fake_list)
    monkeypatch.setattr(sections, "finish", fake_finish)
    monkeypatch.setattr(sessions, "mark_shown", fake_shown)
    monkeypatch.setattr(library, "get_set", no_library)
    monkeypatch.setattr(interview_flow.outbox_service, "flush_quietly", nothing)

    return rows, finished


def test_a_section_with_no_question_left_finishes_and_the_next_opens(interview):
    rows, finished = interview
    first, second = section(answered=True), section()
    rows += [first, second]

    step = asyncio.run(interview_flow.interview_step(first, CANDIDATE))

    assert finished == [first.id]
    assert step.session.id == second.id
    assert step.question is not None and step.question.seconds_left == pytest.approx(30, abs=1)
    assert step.done is False


@pytest.mark.parametrize(("clip", "time_left", "reading_left"), [(12.3, 43, 13), (None, 30, None)])
def test_a_voice_question_is_read_aloud_before_its_time_starts(
    interview, monkeypatch, clip, time_left, reading_left
):
    rows, _ = interview
    rows.append(section())
    rows[0].voice = True

    async def question_clip(row, question):
        if clip is None:
            raise HTTPException(502, "OpenAI is down")

        return SimpleNamespace(seconds=clip)

    monkeypatch.setattr(voice_session, "question_clip", question_clip)

    step = asyncio.run(interview_flow.interview_step(rows[0], CANDIDATE))

    # The question's own 30 seconds start once it's read; a reading that failed adds nothing.
    assert step.question.seconds_left == pytest.approx(time_left, abs=1)
    assert step.question.reading_left == (reading_left and pytest.approx(reading_left, abs=1))


def test_the_last_answer_finishes_the_interview(interview):
    rows, finished = interview
    first, last = section(answered=True, status="finished"), section(answered=True)
    rows += [first, last]

    step = asyncio.run(interview_flow.interview_step(last, CANDIDATE))

    assert finished == [last.id]
    assert step.question is None
    assert step.done is True


def test_finishing_the_interview_ends_every_open_section(interview):
    rows, finished = interview
    rows += [section(answered=True), section()]

    step = asyncio.run(interview_flow.finish_interview(rows[0], CANDIDATE))

    assert finished == [rows[0].id, rows[1].id]
    assert step.done is True
    assert [topic.status for topic in step.topics] == ["finished", "finished"]


def test_a_library_failure_still_gives_the_candidate_their_question(interview, monkeypatch):
    rows, _ = interview
    rows.append(section())

    async def library_down(set_id):
        raise RuntimeError("library is down")

    monkeypatch.setattr(library, "get_set", library_down)

    step = asyncio.run(interview_flow.interview_step(rows[0], CANDIDATE))

    # The clock started, so the question still comes, just without the interview's title.
    assert step.question is not None
    assert step.session.interview_title is None


def test_the_interview_title_is_kept_for_the_next_steps(interview, monkeypatch):
    rows, _ = interview
    rows.append(section())
    asked = []

    async def fake_set(set_id):
        asked.append(set_id)

        return {"title": "Backend", "language": "en"}

    monkeypatch.setattr(library, "get_set", fake_set)

    first = asyncio.run(interview_flow.interview_step(rows[0], CANDIDATE))
    again = asyncio.run(interview_flow.interview_step(rows[0], CANDIDATE))

    assert first.session.interview_title == again.session.interview_title == "Backend"
    assert asked == [rows[0].interview_set_id]


def test_a_step_reads_the_interview_once(interview, monkeypatch):
    rows, _ = interview
    rows += [section(answered=True, status="finished"), section()]
    reads = []

    async def counted_list(session, invite_id):
        reads.append("sections")

        return rows

    async def counted_get(session, session_id):
        reads.append("section")

        return next(row for row in rows if row.id == session_id)

    monkeypatch.setattr(sessions, "list_for_invite", counted_list)
    monkeypatch.setattr(sessions, "get", counted_get)

    step = asyncio.run(interview_flow.interview_step(rows[1], CANDIDATE))

    assert step.session.id == rows[1].id and step.question is not None
    assert [topic.status for topic in step.topics] == ["finished", "in_progress"]
    assert reads == ["sections"]


def test_a_question_whose_time_ran_out_counts_as_wrong_before_the_next_step(interview, monkeypatch):
    rows, _ = interview
    timed_out = section()
    timed_out.question_shown_at = datetime.now(UTC) - timedelta(seconds=60)
    rows += [timed_out, section()]
    saved = []

    async def fake_answer(session, answer, event=None):
        saved.append(answer)
        timed_out.answers = [answer]
        timed_out.question_shown_at = None

        return True

    monkeypatch.setattr(sessions, "add_answer", fake_answer)

    step = asyncio.run(interview_flow.interview_step(rows[1], CANDIDATE))

    # The section's only question counted as wrong, which finished it; the next one opens.
    assert [(answer.timed_out, answer.score) for answer in saved] == [(True, 0)]
    assert step.session.id == rows[1].id
    assert [topic.status for topic in step.topics] == ["finished", "in_progress"]
