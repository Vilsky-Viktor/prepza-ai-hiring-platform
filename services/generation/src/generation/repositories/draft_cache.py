import hashlib
import json
import logging

from langchain_openai import ChatOpenAI

from generation.constants.generation import DRAFT_CACHE_SECONDS
from generation.integrations.redis import get_redis

logger = logging.getLogger(__name__)


def cache_key(kind: str, source: str, model: ChatOpenAI) -> str:
    """`source` holds the whole prompt, and the key the model and its effort, so a changed prompt
    or model never reuses old results."""
    digest = hashlib.sha256(source.encode()).hexdigest()

    return f"draft:{kind}:{model.model_name}:{model.reasoning_effort}:{digest}"


async def get(kind: str, source: str, model: ChatOpenAI) -> dict | list | None:
    """A result saved for the same input, or None. A cache failure only means no cache."""
    try:
        cached = await get_redis().get(cache_key(kind, source, model))
    except Exception:
        logger.exception("Couldn't read the draft cache")

        return None

    return json.loads(cached) if cached else None


async def put(kind: str, source: str, value: dict | list, model: ChatOpenAI) -> None:
    try:
        await get_redis().set(
            cache_key(kind, source, model), json.dumps(value), ex=DRAFT_CACHE_SECONDS
        )
    except Exception:
        logger.exception("Couldn't write the draft cache")
