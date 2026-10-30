import logging
import math

from prepza_common.ai.multi_answer import multi_share
from prepza_common.config.constants import DEFAULT_LANGUAGE

from generation.constants.reuse import MAX_REUSE_SHARE
from generation.helpers.questions import topic_size
from generation.integrations import library
from generation.integrations.redis import get_redis
from generation.integrations.usage import embed
from generation.models.state import State
from generation.schemas.library import ReuseIn

logger = logging.getLogger(__name__)


def topic_text(topic: dict) -> str:
    if not topic["subtopics"]:
        return topic["main_topic"]

    return f"{topic['main_topic']}: {', '.join(topic['subtopics'])}"


async def find_reused(state: State) -> dict:
    """Embeds the approved topics and takes proven questions from similar topics (templates' and,
    for a company's interview, the shared bank's); and sets the run's share of multi-answer
    questions.

    Reuse only saves cost, so any failure here means generating every question instead.
    """
    topics = state["topics"]
    count = math.floor(topic_size(state) * MAX_REUSE_SHARE)
    share = await multi_share(get_redis())

    try:
        embeddings = await embed([topic_text(topic) for topic in topics])
    except Exception:
        logger.exception("Couldn't embed the topics")

        return {"topic_embeddings": [], "reused": [[] for _ in topics], "multi_share": share}

    reused = []
    # A bank question goes into one topic of a test at most, even when two topics are alike; the
    # same text can sit in several templates, so it's told by its text.
    taken = set()

    for embedding in embeddings:
        try:
            found = (
                await library.find_reusable(
                    ReuseIn(
                        embedding=embedding,
                        level=state["level"],
                        language=state.get("language") or DEFAULT_LANGUAGE,
                        count=count,
                        company_id=state.get("company_id"),
                    )
                )
                if count
                else []
            )
        except Exception:
            logger.exception("Couldn't find questions to reuse")
            found = []

        found = [question for question in found if question.text not in taken]
        taken.update(question.text for question in found)
        reused.append([question.model_dump(mode="json") for question in found])

    return {"topic_embeddings": embeddings, "reused": reused, "multi_share": share}
