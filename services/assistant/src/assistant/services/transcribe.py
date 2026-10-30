import logging

from fastapi import HTTPException, Request, status
from openai import OpenAIError
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.secrets_check import SECRET_IN_VOICE, find_secret
from prepza_common.ai.speech import NOTHING_HEARD, audio_seconds, received_audio
from prepza_common.ai.speech import speech_to_text as heard
from prepza_common.limits.pause import refuse_if_paused

from assistant.config import settings
from assistant.constants.ai_usage import TRANSCRIPTION_ACTION
from assistant.constants.limits import MAX_AUDIO_SECONDS
from assistant.constants.transcribe import TRANSCRIBE_FAILED
from assistant.integrations.llm import get_openai
from assistant.integrations.redis import get_redis
from assistant.services import limits
from assistant.services.tenancy import user_companies

logger = logging.getLogger(__name__)


async def speech_to_text(file_name: str, audio: bytes, content_type: str, language: str):
    """OpenAI's transcription of a recording, told the interface's language."""

    return await heard(
        get_openai(), settings.transcribe_model, file_name, audio, content_type, language
    )


async def transcribe(request: Request, user_id: str, language: str) -> str:
    """A voice message's text, heard in the interface's language. Refused during the pause, over
    the limits, for another format (415) or a larger recording (413); nothing heard is a 422.
    Its cost is recorded; the audio and the text are never kept or logged."""
    redis = get_redis()
    await refuse_if_paused(redis, TRANSCRIPTION_ACTION, user_id=user_id)
    content_type, file_name, audio = await received_audio(request)
    await limits.check_transcription(redis, user_id, await user_companies(user_id))
    model = settings.transcribe_model

    try:
        result = await speech_to_text(file_name, audio, content_type, language)
    except OpenAIError as error:
        # The error's type only: its message may quote the request.
        logger.warning("A transcription failed: %s", type(error).__name__)
        await ai_usage.provider_refused(error, TRANSCRIPTION_ACTION, user_id=user_id)
        seconds = audio_seconds(None, len(audio), MAX_AUDIO_SECONDS)
        await ai_usage.record(
            TRANSCRIPTION_ACTION,
            model,
            audio_seconds=seconds,
            user_id=user_id,
            outcome=Outcome.FAILED,
        )
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, TRANSCRIBE_FAILED)

    seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_AUDIO_SECONDS)
    await ai_usage.record(TRANSCRIPTION_ACTION, model, audio_seconds=seconds, user_id=user_id)
    text = result.text.strip()

    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_HEARD)

    # A secret said aloud: its text never comes back.
    if find_secret(text) is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, SECRET_IN_VOICE)

    return text
