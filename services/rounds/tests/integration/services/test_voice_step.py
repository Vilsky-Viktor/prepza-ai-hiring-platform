# Voice mode's step: a question's clock starts once its reading is ready, and the question after
# it is read ahead, across sections too (test_voice_clips.py has the clips themselves).
import asyncio
import uuid

import pytest
from sqlalchemy import update
from testee_common.auth.user import User

from rounds.config import settings
from rounds.core.db import Session as Db
from rounds.core.exceptions import SpeechFailed
from rounds.helpers.voice_speech import clip_key, question_script, saved_answer
from rounds.integrations import library
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.models.voice_clips import VoiceClip
from rounds.repositories import sessions
from rounds.repositories import voice_clips as clip_rows
from rounds.services import interview_flow, voice_clips, voice_session
from tests.integration.factories import answered, created, option_index, topic
from tests.integration.transactions import transaction

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)
AUDIO = b"OggS a question read aloud"
SAVED_TEXTS = {saved_answer(pick, "en") for pick in range(4)}


@pytest.fixture(autouse=True)
def english(monkeypatch):
    async def english_set(set_id):
        return {"title": "Python", "language": "en"}

    monkeypatch.setattr(library, "get_set", english_set)


async def voice_interview(sections=1, size=1):
    """A candidate's voice interview of `sections` sections, `size` questions each, with texts
    no other test reads aloud."""
    topics = [topic(texts=[f"Q {uuid.uuid4()}" for _ in range(size)]) for _ in range(sections)]
    rows = await created("cand", uuid.uuid4(), topics, 60, company_id=uuid.uuid4())

    async with Db.begin() as db:
        await db.execute(
            update(Session).where(Session.id.in_([row.id for row in rows])).values(voice=True)
        )

    return [await transaction(sessions.get, row.id) for row in rows]


async def kept(row: Session, question) -> VoiceClip | None:
    text = question_script(question, "en")
    key = clip_key(settings.speech_model, settings.speech_voice, "en", text)

    async with Db() as db:
        return await clip_rows.get(db, key)


def test_a_voice_questions_clock_starts_once_its_reading_is_kept(run, monkeypatch):
    """OpenAI's reading is held until the test releases it: meanwhile the question has no clock.
    Released, the clip is kept before the clock starts."""
    started, release = asyncio.Event(), asyncio.Event()

    async def speak(text, language):
        started.set()
        await release.wait()

        return AUDIO, 4.0

    monkeypatch.setattr(voice_clips, "speak", speak)

    async def scenario():
        [row] = await voice_interview()
        step = asyncio.create_task(interview_flow.interview_step(row, CANDIDATE))
        await started.wait()
        waiting = await transaction(sessions.get, row.id)
        release.set()
        opened = await step
        clip = await kept(row, opened.question)

        return waiting, await transaction(sessions.get, row.id), clip, opened

    waiting, shown, clip, opened = run(scenario())

    assert waiting.question_shown_at is None
    assert clip is not None and shown.question_shown_at is not None
    assert opened.question.seconds_left == pytest.approx(60, abs=1)


def test_a_question_whose_reading_fails_opens_unread_on_the_clock(run, monkeypatch):
    async def speak(text, language):
        raise SpeechFailed("APIConnectionError", 0.0)

    monkeypatch.setattr(voice_clips, "speak", speak)

    async def scenario():
        [row] = await voice_interview()
        opened = await interview_flow.interview_step(row, CANDIDATE)

        return opened, await kept(row, opened.question), await transaction(sessions.get, row.id)

    opened, clip, shown = run(scenario())

    assert clip is None
    assert shown.question_shown_at is not None
    assert opened.question.seconds_left == pytest.approx(60, abs=1)


def test_a_sections_last_question_reads_the_next_sections_first_ahead(run, monkeypatch):
    read = []

    async def speak(text, language):
        read.append(text)

        return AUDIO, 4.0

    monkeypatch.setattr(voice_clips, "speak", speak)

    async def scenario():
        first, second = await voice_interview(sections=2)
        opened = await interview_flow.interview_step(first, CANDIDATE)
        await voice_session.prepare_next(await transaction(sessions.get, first.id))
        # Answered, the step opens the next section's question with its clip kept: no reading.
        question = first.questions[0]
        await answered(
            Answer(
                session_id=first.id,
                question_id=uuid.UUID(question["id"]),
                option_index=option_index(question, True),
                correct=True,
                score=100,
            )
        )
        read_before = len(read)
        following = await interview_flow.interview_step(
            await transaction(sessions.get, first.id), CANDIDATE
        )

        return opened, following, second, read_before

    opened, following, second, read_before = run(scenario())
    # The interviewer's "B, saved." clips are made ahead too, once for every interview.
    questions = [text for text in read if text not in SAVED_TEXTS]

    assert opened.question.last is False
    assert following.session.id == second.id
    assert following.question.last is True
    # One reading of each question: the second's made ahead, not again when it opened.
    assert len(read) == read_before
    assert len(questions) == 2
    assert following.question.text in questions[1]


def test_a_questions_saved_answers_are_kept_ahead_for_every_interview(run, monkeypatch):
    """Each option's "{letter}, saved." is kept as the question opens, the interviewer's own
    (no company's), so a clear answer is told without waiting."""

    async def speak(text, language):
        return AUDIO, 1.0

    monkeypatch.setattr(voice_clips, "speak", speak)

    async def scenario():
        [row] = await voice_interview()
        opened = await interview_flow.interview_step(row, CANDIDATE)
        await voice_session.prepare_next(await transaction(sessions.get, row.id))
        found = []

        for pick in range(len(opened.question.options)):
            key = clip_key(
                settings.speech_model, settings.speech_voice, "en", saved_answer(pick, "en")
            )

            async with Db() as db:
                found.append(await clip_rows.get(db, key))

        return found

    found = run(scenario())

    assert found and all(clip is not None and clip.company_id is None for clip in found)
