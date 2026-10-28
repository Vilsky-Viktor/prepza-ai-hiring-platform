from fastapi import HTTPException, status

from generation.constants.generation import RUN_GENERATION
from generation.core.db import Session
from generation.integrations import tasks
from generation.models.generation import Generation
from generation.repositories import generations


async def retry_generation(generation: Generation) -> Generation:
    """Queues a failed generation again; the worker continues from its last checkpoint."""
    async with Session.begin() as session:
        claimed = await generations.claim_retry(session, generation.id)

    if not claimed:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a failed generation can be retried")

    await tasks.enqueue(RUN_GENERATION, {"generation_id": str(generation.id)})

    async with Session() as session:
        return await generations.get(session, generation.id)
