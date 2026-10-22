import logging
import random
from uuid import UUID

from prepza_common.capped import gather_capped
from prepza_common.limits import limit

from app.constants.actions import SAMPLE_KEY_CHECK
from app.constants.quality import KEY_CHECKS_PER_TOPIC
from app.helpers.questions import set_company
from app.integrations import library
from app.integrations.redis import get_redis
from app.integrations.usage import ai_run
from app.services.verify import check_key

logger = logging.getLogger(__name__)


async def check_one(question_id: UUID) -> None:
    context = await library.get_question_context(question_id)
    question = await library.get_question_quality(question_id)

    if context is None or question is None:
        return

    async with ai_run(SAMPLE_KEY_CHECK, set_company(context), subject_id=question_id):
        await check_key(question_id, question, context)


async def check_sample(set_id: UUID) -> None:
    """Before a new test or template is ready, the verifier checks a few random answer keys of
    each topic, and fixes or replaces what's wrong. Never raises: a check that fails mustn't
    fail the generation."""
    try:
        topics = await library.get_question_ids(set_id)
    except Exception:
        logger.exception("Couldn't check the answer keys of set %s", set_id)

        return

    await check_topics(topics)


async def check_topics(topics: list[list[UUID]]) -> None:
    """A few random answer keys of each topic's questions, checked as check_sample does; also
    for the questions an addition adds to a template. Never raises."""
    try:
        sample = [
            question_id
            for question_ids in topics
            for question_id in random.sample(
                question_ids, min(KEY_CHECKS_PER_TOPIC, len(question_ids))
            )
        ]
        results = await gather_capped(
            await limit(get_redis(), "GENERATION_CALLS_AT_ONCE"),
            (check_one(question_id) for question_id in sample),
            return_exceptions=True,
        )
    except Exception:
        logger.exception("Couldn't check the answer keys")

        return

    for question_id, result in zip(sample, results):
        if isinstance(result, Exception):
            logger.warning("Couldn't check question %s: %s", question_id, result)
