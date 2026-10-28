from collections.abc import Awaitable, Callable
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from library.core.db import Session
from library.repositories import preparations


async def saved_by(generation_id: UUID) -> UUID | None:
    async with Session() as session:
        return await preparations.find_by_generation(session, generation_id)


async def save_once(generation_id: UUID, create: Callable[[], Awaitable[UUID]]) -> UUID:
    """The set a generation saved, made by `create` (its own transaction) the first time. Two
    saves at once can both find none: the second's insert breaks a unique constraint
    (sets.generation_id, or the slug the first took), and it returns the first's set or, for the
    slug, tries the next one."""
    existing = await saved_by(generation_id)

    if existing:
        return existing

    try:
        return await create()
    except IntegrityError:
        return await saved_by(generation_id) or await create()
