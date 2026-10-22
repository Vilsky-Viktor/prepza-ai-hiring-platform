from uuid import UUID

from sqlalchemy import Uuid, column, update, values

from app.models.sessions import Session
from app.storage.db import Session as Db


async def fill(companies: dict[UUID, UUID]) -> int:
    """Gives the sections of each interview set (by its id) their company where they have none,
    in one statement: the sections started before rounds kept it. Safe to repeat; how many it
    filled."""
    if not companies:
        return 0

    given = values(column("set_id", Uuid), column("company_id", Uuid), name="given").data(
        list(companies.items())
    )
    query = (
        update(Session)
        .where(
            Session.interview_set_id == given.c.set_id,
            Session.company_id.is_(None),
            Session.practice.is_(False),
        )
        .values(company_id=given.c.company_id)
    )

    async with Db() as session:
        done = await session.execute(query)
        await session.commit()

    return done.rowcount
