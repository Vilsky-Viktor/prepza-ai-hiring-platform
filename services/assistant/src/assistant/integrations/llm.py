from functools import cache

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from prepza_common.ai.llm import chat_model

from assistant.config import settings
from assistant.constants.chat import (
    MAX_ANSWER_TOKENS,
    MODEL_INCLUDE,
    MODEL_RETRIES,
    MODEL_TIMEOUT_SECONDS,
)
from assistant.constants.help_chat import HELP_MAX_OUTPUT_TOKENS, HELP_RETRIES, HELP_TIMEOUT_SECONDS
from assistant.constants.titles import TITLE_MAX_TOKENS
from assistant.constants.tool_groups import (
    ROUTING_MAX_TOKENS,
    ROUTING_RETRIES,
    ROUTING_TIMEOUT_SECONDS,
)
from assistant.constants.transcribe import TRANSCRIBE_RETRIES, TRANSCRIBE_TIMEOUT_SECONDS


@cache
def get_chat_model() -> ChatOpenAI:
    """The assistant's model; it reports each call's tokens as it streams."""
    return chat_model(
        settings.assistant_model,
        settings.assistant_reasoning_effort,
        stream_usage=True,
        max_tokens=MAX_ANSWER_TOKENS,
        include=MODEL_INCLUDE,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_RETRIES,
    )


@cache
def get_openai() -> AsyncOpenAI:
    """OpenAI's own client, for speech to text."""
    return AsyncOpenAI(
        api_key=settings.openai_api_key or None,
        timeout=TRANSCRIBE_TIMEOUT_SECONDS,
        max_retries=TRANSCRIBE_RETRIES,
    )


@cache
def get_routing_model() -> ChatOpenAI:
    """The groups of tools a turn is offered: a few tokens."""
    return chat_model(
        settings.routing_model,
        settings.routing_reasoning_effort,
        max_tokens=ROUTING_MAX_TOKENS,
        timeout=ROUTING_TIMEOUT_SECONDS,
        max_retries=ROUTING_RETRIES,
    )


@cache
def get_title_model() -> ChatOpenAI:
    """The conversations' titles: a few tokens."""
    return chat_model(
        settings.title_model,
        settings.title_reasoning_effort,
        max_tokens=TITLE_MAX_TOKENS,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_RETRIES,
    )


@cache
def get_help_llm() -> ChatOpenAI:
    """The help chat's model; at effort "none" it answers at a low temperature."""
    return chat_model(
        settings.help_model,
        settings.help_reasoning_effort,
        temperature=0.3,
        max_retries=HELP_RETRIES,
        timeout=HELP_TIMEOUT_SECONDS,
        max_tokens=HELP_MAX_OUTPUT_TOKENS,
        # The last chunk carries the answer's tokens, for the daily budget.
        stream_usage=True,
    )
