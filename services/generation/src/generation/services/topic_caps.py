"""MAX_TOPICS and MAX_SUBTOPICS as set in Controls now: what the topic draft is held to, what a
review may approve, and what the review page is told."""

from prepza_common.limits.limits import limit

from generation.integrations.redis import get_redis
from generation.models.generation import Generation
from generation.schemas.generation import GenerationOut


async def topic_caps() -> dict:
    redis = get_redis()

    return {
        "max_topics": await limit(redis, "MAX_TOPICS"),
        "max_subtopics": await limit(redis, "MAX_SUBTOPICS"),
    }


async def generation_out(generation: Generation) -> GenerationOut:
    return GenerationOut.model_validate(generation).model_copy(update=await topic_caps())
