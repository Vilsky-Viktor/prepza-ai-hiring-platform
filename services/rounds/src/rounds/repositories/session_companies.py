from uuid import UUID

from sqlalchemy import Uuid, column, update, values
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.models.sessions import Session as RoundSession


async def fill(session: AsyncSession, companies: dict[UUID, UUID]) -> int:
    """Gives the sections of each interview set (by its id) their company where they have none,
    in one statement: the sections started before rounds kept it. Safe to repeat; how many it
    filled."""
    if not companies:
        return 0

    given = values(column("set_id", Uuid), column("company_id", Uuid), name="given").data(
        list(companies.items())
    )
    query = (
        update(RoundSession)
        .where(
            RoundSession.interview_set_id == given.c.set_id,
            RoundSession.company_id.is_(None),
            RoundSession.practice.is_(False),
        )
        .values(company_id=given.c.company_id)
    )

    done = await session.execute(query)

    return done.rowcount
