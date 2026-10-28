from uuid import UUID

from rounds.core.db import Session
from rounds.repositories import session_companies


async def fill(companies: dict[UUID, UUID]) -> int:
    """Companies' backfill: the company of each interview set, for the sections started before
    rounds kept it; how many it filled."""
    async with Session.begin() as session:
        return await session_companies.fill(session, companies)
