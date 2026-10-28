from fastapi import HTTPException, status

from generation.constants.generation import RUN_GENERATION
from generation.integrations import tasks
from generation.models.generation import Generation
from generation.repositories import generations


async def retry_generation(generation: Generation) -> Generation:
    """Queues a failed generation again; the worker continues from its last checkpoint."""
    if not await generations.claim_retry(generation.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a failed generation can be retried")

    await tasks.enqueue(RUN_GENERATION, {"generation_id": str(generation.id)})

    return await generations.get(generation.id)
