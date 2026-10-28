"""A running generation's row, read and saved between model calls: each change in a transaction
of its own, so progress is kept as the run goes and nothing is held open across a call."""

import uuid

from generation.core.db import Session
from generation.repositories import generations


async def is_cancelled(generation_id: uuid.UUID) -> bool:
    async with Session() as session:
        return await generations.is_cancelled(session, generation_id)


async def save(generation_id: uuid.UUID, event: tuple[str, dict] | None = None, **values) -> bool:
    """See `generations.update`: a finished generation is left as it is (False)."""
    async with Session.begin() as session:
        return await generations.update(session, generation_id, event, **values)
