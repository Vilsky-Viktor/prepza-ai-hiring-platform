import logging

from fastapi import HTTPException, Request, status
from openai import OpenAIError
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.secrets_check import SECRET_IN_VOICE, find_secret
from prepza_common.limits.pause import refuse_if_paused

from assistant.config import settings
from assistant.constants.ai_usage import TRANSCRIPTION_ACTION
from assistant.constants.transcribe import (
    AUDIO_FILES,
    AUDIO_NOT_SUPPORTED,
    AUDIO_SIGNATURES,
    AUDIO_TOO_LARGE,
    MAX_AUDIO_BYTES,
    NOTHING_HEARD,
    TRANSCRIBE_FAILED,
    TRANSCRIBE_LANGUAGES,
)
from assistant.helpers.audio import audio_seconds
from assistant.integrations.llm import get_openai
from assistant.integrations.redis import get_redis
from assistant.services import limits
from assistant.services.tenancy import user_companies

logger = logging.getLogger(__name__)


async def read_audio(request: Request) -> bytes:
    """The recording in the request's body, in memory; over MAX_AUDIO_BYTES, a 413 before more
    of it is read."""
    if int(request.headers.get("content-length") or 0) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, AUDIO_TOO_LARGE)

    audio = bytearray()

    async for chunk in request.stream():
        audio += chunk

        if len(audio) > MAX_AUDIO_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, AUDIO_TOO_LARGE)

    return bytes(audio)


async def speech_to_text(file_name: str, audio: bytes, content_type: str, language: str):
    """OpenAI's transcription of a recording, told the interface's language."""

    return await get_openai().audio.transcriptions.create(
        model=settings.transcribe_model,
        file=(file_name, audio, content_type),
        languages=[TRANSCRIBE_LANGUAGES.get(language, language)],
    )


async def transcribe(request: Request, user_id: str, language: str) -> str:
    """A voice message's text, heard in the interface's language. Refused during the pause, over
    the limits, for another format (415) or a larger recording (413); nothing heard is a 422.
    Its cost is recorded; the audio and the text are never kept or logged."""
    redis = get_redis()
    await refuse_if_paused(redis, TRANSCRIPTION_ACTION, user_id=user_id)
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    file_name = AUDIO_FILES.get(content_type)

    if file_name is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, AUDIO_NOT_SUPPORTED)

    audio = await read_audio(request)

    if not audio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_HEARD)

    offset, signature = AUDIO_SIGNATURES[content_type]

    if audio[offset : offset + len(signature)] != signature:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, AUDIO_NOT_SUPPORTED)

    await limits.check_transcription(redis, user_id, await user_companies(user_id))
    model = settings.transcribe_model

    try:
        result = await speech_to_text(file_name, audio, content_type, language)
    except OpenAIError as error:
        # The error's type only: its message may quote the request.
        logger.warning("A transcription failed: %s", type(error).__name__)
        await ai_usage.provider_refused(error, TRANSCRIPTION_ACTION, user_id=user_id)
        seconds = audio_seconds(None, len(audio))
        await ai_usage.record(
            TRANSCRIPTION_ACTION,
            model,
            audio_seconds=seconds,
            user_id=user_id,
            outcome=Outcome.FAILED,
        )
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, TRANSCRIBE_FAILED)

    seconds = audio_seconds(getattr(result, "usage", None), len(audio))
    await ai_usage.record(TRANSCRIPTION_ACTION, model, audio_seconds=seconds, user_id=user_id)
    text = result.text.strip()

    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_HEARD)

    # A secret said aloud: its text never comes back.
    if find_secret(text) is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, SECRET_IN_VOICE)

    return text
