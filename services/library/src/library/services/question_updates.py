from datetime import datetime

from library.core.db import Session
from library.repositories import question_updates


async def between(
    company_ids: list[str], since: datetime, until: datetime, limit: int
) -> tuple[list[tuple], dict[str, int]]:
    """The newest `limit` updates of each kind to the companies' interviews' questions, and how
    many of each kind there are in all (repositories/question_updates.py)."""
    async with Session() as session:
        rows = await question_updates.between(session, company_ids, since, until, limit)

        return rows, await question_updates.counts(session, company_ids, since, until)
