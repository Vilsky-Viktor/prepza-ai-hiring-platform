from functools import cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prepza_common.llm import chat_model

from app.config.settings import settings
from app.constants.generation import LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS, MAX_OUTPUT_TOKENS
from app.constants.reuse import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from app.integrations.llm_limiter import SharedRateLimiter


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


@cache
def get_rate_limiter() -> SharedRateLimiter:
    return SharedRateLimiter()


@cache
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=LLM_MAX_RETRIES,
    )
