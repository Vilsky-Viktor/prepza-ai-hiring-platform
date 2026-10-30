import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update

from rounds.core.db import Session as Db
from rounds.models.answers import Answer
from rounds.models.voice_clips import VoiceClip
from rounds.repositories import sessions
from rounds.services import session_removal, voice_clips
from tests.integration.factories import answered, created, topic
from tests.integration.transactions import transaction

# What OpenAI's reading gives: an Ogg Opus clip (its length isn't read here).
AUDIO = b"OggS a clip read aloud"


async def voice_section(company_id=None):
    [row] = await created(
        "cand", uuid.uuid4(), [topic()], 60, company_id=company_id or uuid.uuid4()
    )

    return row


def reading(monkeypatch):
    """OpenAI's reading faked; the texts it was asked to read."""
    read = []

    async def speak(text):
        read.append(text)

        return AUDIO

    monkeypatch.setattr(voice_clips, "speak", speak)

    return read


async def clips_of(*keys):
    async with Db() as db:
        return list(await db.scalars(select(VoiceClip).where(VoiceClip.key.in_(keys))))


def test_a_text_is_read_aloud_once_for_every_candidate(run, monkeypatch, published):
    read = reading(monkeypatch)
    text = f"Which measure ignores outliers? {uuid.uuid4()}"

    async def scenario():
        first = await voice_clips.clip_for(await voice_section(), text, "en", company_text=True)
        again = await voice_clips.clip_for(await voice_section(), text, "en", company_text=True)

        return first, again

    first, again = run(scenario())

    assert read == [text]
    assert again.id == first.id and again.audio == AUDIO
    assert [kind for kind, data in published if data.get("action") == "voice_speech"] == ["ai.used"]


def test_two_readings_of_one_text_at_once_keep_one_clip(run, monkeypatch):
    reading(monkeypatch)
    text = f"A phrase {uuid.uuid4()}"

    async def scenario():
        row = await voice_section()
        made = await asyncio.gather(
            voice_clips.clip_for(row, text, "en", company_text=False),
            voice_clips.clip_for(row, text, "en", company_text=False),
        )

        async with Db() as db:
            count = await db.scalar(select(func.count()).where(VoiceClip.id == made[0].id))

        return made, count

    (one, other), count = run(scenario())

    assert one.id == other.id and count == 1
    # The interviewer's phrases belong to no company.
    assert one.company_id is None


def test_a_deleted_company_takes_its_questions_clips_but_not_the_phrases(run, monkeypatch):
    reading(monkeypatch)
    gone, kept = uuid.uuid4(), uuid.uuid4()

    async def scenario():
        gone_row, kept_row = await voice_section(gone), await voice_section(kept)
        question = await voice_clips.clip_for(gone_row, f"Q {gone}", "en", company_text=True)
        phrase = await voice_clips.clip_for(gone_row, f"P {gone}", "en", company_text=False)
        other = await voice_clips.clip_for(kept_row, f"Q {kept}", "en", company_text=True)
        await session_removal.remove_company(gone)
        # A redelivered company.deleted changes nothing more.
        await session_removal.remove_company(gone)

        return {c.id for c in await clips_of(question.key, phrase.key, other.key)}, (
            question.id,
            phrase.id,
            other.id,
        )

    left, (question, phrase, other) = run(scenario())

    assert left == {phrase, other}
    assert question not in left


def test_clips_nobody_played_for_their_days_go_and_a_played_one_stays(run, monkeypatch):
    reading(monkeypatch)
    stamp = uuid.uuid4()

    async def scenario():
        row = await voice_section()
        old = await voice_clips.clip_for(row, f"old {stamp}", "en", company_text=True)
        played = await voice_clips.clip_for(row, f"played {stamp}", "en", company_text=True)
        long_ago = datetime.now(UTC) - timedelta(days=31)

        async with Db.begin() as db:
            await db.execute(
                update(VoiceClip)
                .where(VoiceClip.id.in_([old.id, played.id]))
                .values(used_at=long_ago)
            )

        # Played again: its last use is brought up to date.
        await voice_clips.clip_for(row, f"played {stamp}", "en", company_text=True)
        await voice_clips.remove_unused(30)

        return {c.id for c in await clips_of(old.key, played.key)}, played.id

    left, played = run(scenario())

    assert left == {played}


def test_a_question_read_aloud_keeps_its_reading_until_answered(run):
    async def scenario():
        row = await voice_section()
        first = await transaction(sessions.mark_shown, row.id, 12)
        # A reload asks again: the same start and reading.
        again = await transaction(sessions.mark_shown, row.id, 40)
        question_id = uuid.UUID(row.questions[0]["id"])
        answer = Answer(
            session_id=row.id, question_id=question_id, option_index=0, correct=True, score=100
        )
        await answered(answer)

        return first, again, await transaction(sessions.get, row.id)

    first, again, row = run(scenario())

    assert first == again and first[1] == 12
    assert (row.question_shown_at, row.question_reading_seconds) == (None, None)
