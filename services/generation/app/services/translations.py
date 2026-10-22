# Translating prepza's own texts (news posts, campaigns) into every language they lack, with the
# generation model; each kind gives its prompt, its fields' limits and where it's saved.
import logging
from collections.abc import Awaitable, Callable

from langchain_core.messages import HumanMessage, SystemMessage
from prepza_common.capped import gather_capped
from prepza_common.limits import limit
from pydantic import BaseModel

from app.integrations import llm
from app.integrations.redis import get_redis

logger = logging.getLogger(__name__)


async def translate_fields[T: BaseModel](
    schema: type[T], system: str, request: str, limits: dict[str, int], language: str
) -> T:
    """The model's translation of `request` (the text, tagged, and the language) under the
    kind's `system` rules, trimmed; raises when a field in `limits` is empty or longer than its
    limit."""
    structured_llm = llm.get_translation_llm().with_structured_output(schema)
    messages = [SystemMessage(content=system), HumanMessage(content=request)]
    result = await structured_llm.ainvoke(messages)
    values = {
        name: value.strip() if isinstance(value, str) else value
        for name, value in result.model_dump().items()
    }

    for name, longest in limits.items():
        if not values[name]:
            raise ValueError(f"Empty {language} translation")

        if len(values[name]) > longest:
            raise ValueError(f"The {language} translation is too long")

    return schema(**values)


async def translate_missing[T](
    what: str,
    missing: list[str],
    translate: Callable[[str], Awaitable[T]],
    save: Callable[[dict[str, T]], Awaitable[None]],
) -> None:
    """Translates into each missing language, GENERATION_CALLS_AT_ONCE at a time, and saves
    those that worked. Raises when a
    language failed, so Cloud Tasks runs the job again for the ones still missing; until then
    those languages show the English. Safe to repeat."""
    results = await gather_capped(
        await limit(get_redis(), "GENERATION_CALLS_AT_ONCE"),
        (translate(language) for language in missing),
        return_exceptions=True,
    )
    done = {}

    for language, result in zip(missing, results, strict=True):
        if isinstance(result, BaseException):
            logger.warning("Couldn't translate %s into %s: %s", what, language, result)
        else:
            done[language] = result

    if done:
        await save(done)

    if len(done) < len(missing):
        raise RuntimeError(f"{what}: {len(missing) - len(done)} languages left")
