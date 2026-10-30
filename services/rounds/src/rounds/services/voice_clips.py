import asyncio
import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from openai import OpenAIError
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.config.constants import LANGUAGES
from prepza_common.redis import redis_lock

from rounds.config import settings
from rounds.constants.voice import (
    CLIP_LOCK_SECONDS,
    CLIP_TOUCH_HOURS,
    CLIP_WAIT_SECONDS,
    SPEECH_ACTION,
    SPEECH_ATTEMPTS,
    SPEECH_FAILED,
)
from rounds.core.db import Session as Db
from rounds.core.exceptions import SpeechFailed
from rounds.helpers.voice_speech import clip_key, ogg_opus, ogg_seconds, pcm_seconds, strays
from rounds.integrations.redis import get_redis
from rounds.integrations.speech import say
from rounds.models.sessions import Session
from rounds.models.voice_clips import VoiceClip
from rounds.prompts.voice_speech import READING
from rounds.repositories import voice_clips
from rounds.services import voice_limits

logger = logging.getLogger(__name__)


async def speak(text: str, language: str) -> tuple[bytes, float]:
    """OpenAI's reading of `text` in the interview's language, as Ogg Opus, and the seconds of
    speech made for it. A reading that fails or strays from the text (by the model's own
    transcript: an answer added, words left out) is made again, SPEECH_ATTEMPTS times at most;
    then SpeechFailed, with the seconds spent."""
    instructions = READING.format(language=LANGUAGES[language], text=text)
    spent = 0.0
    reason = ""

    for _ in range(SPEECH_ATTEMPTS):
        try:
            pcm, transcript = await say(instructions)
        except (SpeechFailed, OpenAIError, TimeoutError, OSError) as error:
            reason = type(error).__name__
            continue

        spent += pcm_seconds(pcm)

        if not strays(text, transcript):
            return await asyncio.to_thread(ogg_opus, pcm), spent

        reason = "strayed"

    raise SpeechFailed(reason, spent)


async def cached(key: str) -> VoiceClip | None:
    """The clip, its last use brought up to date at most every CLIP_TOUCH_HOURS."""
    now = datetime.now(UTC)

    async with Db() as session:
        found = await voice_clips.get(session, key)

    if found is not None and found.used_at < now - timedelta(hours=CLIP_TOUCH_HOURS):
        async with Db.begin() as session:
            await voice_clips.touch(session, found.id, now)

    return found


def lock_of(key: str) -> str:
    """The Redis lock held while a clip is read aloud, so one text is paid for once."""
    return f"voice:clip_lock:{key}"


async def made_elsewhere(key: str) -> None:
    """Waits while another request reads the same text aloud (holds its lock), at most
    CLIP_LOCK_SECONDS."""
    redis = get_redis()

    for _ in range(int(CLIP_LOCK_SECONDS / CLIP_WAIT_SECONDS)):
        if not await redis.exists(lock_of(key)):
            return

        await asyncio.sleep(CLIP_WAIT_SECONDS)


async def clip_for(row: Session, text: str, language: str, company_text: bool) -> VoiceClip:
    """`text` read aloud: the clip kept from before, or read now (counted against the limits,
    priced) and kept for every candidate after. `company_text`: a question of the company's,
    deleted with it; otherwise one of the interviewer's phrases. While another request reads
    the same text, its clip is waited for rather than paid for twice. 502 when OpenAI fails."""
    key = clip_key(settings.speech_model, settings.speech_voice, language, text)
    found = await cached(key)

    if found is not None:
        return found

    token = await redis_lock.acquire(get_redis(), lock_of(key), CLIP_LOCK_SECONDS)

    if token is None:
        await made_elsewhere(key)

        return await cached(key) or await made(row, key, text, language, company_text)

    return await made_once(row, key, text, language, company_text, token)


async def made_ahead(row: Session, text: str, language: str, company_text: bool) -> None:
    """clip_for, ahead of time: nothing when the clip is kept or another request is reading it
    aloud now."""
    key = clip_key(settings.speech_model, settings.speech_voice, language, text)

    if await cached(key) is not None:
        return

    token = await redis_lock.acquire(get_redis(), lock_of(key), CLIP_LOCK_SECONDS)

    if token is not None:
        await made_once(row, key, text, language, company_text, token)


async def made_once(
    row: Session, key: str, text: str, language: str, company_text: bool, token: str
) -> VoiceClip:
    """Under the clip's lock (`token`): the clip, unless another request kept it just before."""
    try:
        return await cached(key) or await made(row, key, text, language, company_text)
    finally:
        await redis_lock.release(get_redis(), lock_of(key), token)


async def made(row: Session, key: str, text: str, language: str, company_text: bool) -> VoiceClip:
    """`text` read aloud now, counted against the limits, priced and kept."""
    await voice_limits.check_clip(row)
    who = {"company_id": row.company_id, "user_id": row.user_id, "subject_id": row.id}
    model = settings.speech_model

    try:
        audio, spent = await speak(text, language)
    except SpeechFailed as error:
        logger.warning("Reading a clip aloud failed: %s", error)
        await ai_usage.record(
            SPEECH_ACTION, model, audio_seconds=error.seconds, outcome=Outcome.FAILED, **who
        )
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, SPEECH_FAILED)

    await ai_usage.record(SPEECH_ACTION, model, audio_seconds=spent, **who)
    seconds = ogg_seconds(audio)
    clip = VoiceClip(
        key=key,
        company_id=row.company_id if company_text else None,
        audio=audio,
        seconds=seconds,
    )

    async with Db.begin() as session:
        return await voice_clips.add(session, clip)


async def remove_company(company_id) -> int:
    """A deleted company's clips (company.deleted); safe to repeat."""
    return await voice_clips.remove_for_company(Db, company_id)


async def remove_unused(days: int, until: float | None = None) -> int:
    """Clips nobody has played for `days` days."""
    return await voice_clips.remove_unused(Db, datetime.now(UTC) - timedelta(days=days), until)
