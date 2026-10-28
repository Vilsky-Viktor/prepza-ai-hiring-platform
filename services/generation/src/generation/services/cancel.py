from fastapi import HTTPException, status

from generation.models.generation import Generation
from generation.repositories import generations


async def cancel_generation(generation: Generation) -> Generation:
    """Cancels a generation that hasn't finished.

    A job already running notices at its next step and stops without saving its test.
    """
    if not await generations.cancel(generation.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Generation already finished")

    return await generations.get(generation.id)
