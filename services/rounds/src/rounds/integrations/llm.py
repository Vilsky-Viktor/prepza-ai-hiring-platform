from functools import cache

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from prepza_common.ai.llm import chat_model

from rounds.config import settings
from rounds.constants.voice import (
    MATCH_MAX_TOKENS,
    MATCH_RETRIES,
    MATCH_TIMEOUT_SECONDS,
    SPEECH_RETRIES,
    SPEECH_TIMEOUT_SECONDS,
    TRANSCRIBE_RETRIES,
    TRANSCRIBE_TIMEOUT_SECONDS,
)


@cache
def get_match_model() -> ChatOpenAI:
    """Turns a spoken answer into options: a few tokens."""
    return chat_model(
        settings.voice_match_model,
        settings.voice_match_reasoning_effort,
        max_tokens=MATCH_MAX_TOKENS,
        timeout=MATCH_TIMEOUT_SECONDS,
        max_retries=MATCH_RETRIES,
    )


@cache
def get_speech_client() -> AsyncOpenAI:
    """OpenAI's own client, for reading text aloud."""
    return AsyncOpenAI(
        api_key=settings.openai_api_key or None,
        timeout=SPEECH_TIMEOUT_SECONDS,
        max_retries=SPEECH_RETRIES,
    )


@cache
def get_transcribe_client() -> AsyncOpenAI:
    """OpenAI's own client, for hearing a spoken answer."""
    return AsyncOpenAI(
        api_key=settings.openai_api_key or None,
        timeout=TRANSCRIBE_TIMEOUT_SECONDS,
        max_retries=TRANSCRIBE_RETRIES,
    )
