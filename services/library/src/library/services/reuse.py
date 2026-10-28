import uuid

from library.core.db import Session
from library.repositories import reuse


async def save_embeddings(embeddings: dict[uuid.UUID, list[float]]) -> None:
    """Topics' embeddings, from generation's embed_templates job."""
    async with Session.begin() as session:
        await reuse.save(session, embeddings)
