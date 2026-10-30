from functools import cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prepza_common.ai.llm import chat_model

from generation.config import settings
from generation.constants.generation import LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS, MAX_OUTPUT_TOKENS
from generation.constants.reuse import EMBEDDING_DIMENSIONS
from generation.constants.screen import SCREEN_MAX_TOKENS, SCREEN_RETRIES, SCREEN_TIMEOUT_SECONDS
from generation.integrations.llm_limiter import SharedRateLimiter


@cache
def build_llm(model: str, reasoning_effort: str) -> ChatOpenAI:
    return chat_model(
        model,
        reasoning_effort,
        max_retries=LLM_MAX_RETRIES,
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=LLM_TIMEOUT_SECONDS,
        rate_limiter=get_rate_limiter(),
    )


def get_generation_llm() -> ChatOpenAI:
    return build_llm(settings.interview_model, settings.interview_reasoning_effort)


def get_verifier_llm() -> ChatOpenAI:
    return build_llm(settings.verify_model, settings.verify_reasoning_effort)


def get_translation_llm() -> ChatOpenAI:
    return build_llm(settings.translation_model, settings.translation_reasoning_effort)


def get_patterns_llm() -> ChatOpenAI:
    return build_llm(settings.patterns_model, settings.patterns_reasoning_effort)


@cache
def get_screen_llm() -> ChatOpenAI:
    """The check before a generation: the user waits on it, so its own short timeout."""
    return chat_model(
        settings.screen_model,
        settings.screen_reasoning_effort,
        max_retries=SCREEN_RETRIES,
        max_tokens=SCREEN_MAX_TOKENS,
        timeout=SCREEN_TIMEOUT_SECONDS,
    )


def get_bank_filter_llm() -> ChatOpenAI:
    return build_llm(settings.bank_filter_model, settings.bank_filter_reasoning_effort)


def get_code_tags_llm() -> ChatOpenAI:
    return build_llm(settings.code_tags_model, settings.code_tags_reasoning_effort)


@cache
def get_rate_limiter() -> SharedRateLimiter:
    return SharedRateLimiter()


@cache
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        dimensions=EMBEDDING_DIMENSIONS,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=LLM_MAX_RETRIES,
    )
