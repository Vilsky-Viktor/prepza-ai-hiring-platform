import asyncio
import logging
import operator

from generation.constants.generation import DUPLICATE_DISTANCE
from generation.integrations.usage import embed

logger = logging.getLogger(__name__)


async def distinct_by_meaning(texts: list[str], keep_first: int = 0) -> list[int]:
    """Indexes of the texts to keep, dropping any that ask what an earlier kept one asks.

    The first `keep_first` texts are always kept. Without embeddings, every text is kept.
    """
    try:
        vectors = await embed(texts)
    except Exception:
        logger.exception("Couldn't embed questions to drop duplicates")

        return list(range(len(texts)))

    # Comparing every pair is pure CPU: off the event loop, so the instance's other requests and
    # jobs aren't held while it runs.
    return await asyncio.to_thread(distinct, vectors, keep_first)


def distinct(vectors: list[list[float]], keep_first: int) -> list[int]:
    """Indexes of the vectors to keep, the first `keep_first` always, then each one far enough
    from every one kept before it."""
    kept = list(range(min(keep_first, len(vectors))))

    for index in range(len(kept), len(vectors)):
        # OpenAI embeddings have length 1, so the dot product is the cosine similarity.
        if all(
            1 - sum(map(operator.mul, vectors[index], vectors[other])) > DUPLICATE_DISTANCE
            for other in kept
        ):
            kept.append(index)

    return kept
