"""Embeds template and company test topics that have no embedding (templates copied in by hand,
tests saved before their embeddings were kept), so the question bank can match them by
meaning. Safe to run again: it only picks topics still missing one.

Run from the repo root:
    docker-compose exec generation uv run --no-sync python -m generation.jobs.embed_templates
"""

import asyncio
import logging

from testee_common.observability.logging import configure_logging

from generation.constants.reuse import EMBEDDING_BATCH_SIZE
from generation.integrations import library
from generation.integrations.usage import embed
from generation.services.nodes.reuse import topic_text

logger = logging.getLogger(__name__)


async def embed_templates() -> int:
    done = 0

    while topics := await library.missing_embeddings(EMBEDDING_BATCH_SIZE):
        texts = [
            topic_text({"main_topic": t["title"], "subtopics": t["subtopics"]}) for t in topics
        ]
        vectors = await embed(texts)
        await library.save_embeddings(
            {topic["id"]: vector for topic, vector in zip(topics, vectors)}
        )
        done += len(topics)

    return done


if __name__ == "__main__":
    configure_logging()
    print(f"Embedded {asyncio.run(embed_templates())} topics")
