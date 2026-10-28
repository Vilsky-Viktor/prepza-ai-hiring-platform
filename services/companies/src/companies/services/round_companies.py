"""One-off: gives rounds the company of every interview's sections started before rounds kept
it (migration rounds 0029), a batch of interviews at a time. Safe to run again.
Run: python -m companies.services.round_companies"""

import asyncio
import logging

from companies.constants.reports import READ_BATCH
from companies.core.db import Session
from companies.integrations import rounds
from companies.repositories import interviews

logger = logging.getLogger(__name__)


async def read_batch(after) -> list[tuple]:
    async with Session() as session:
        return await interviews.set_companies(session, after, READ_BATCH)


async def backfill() -> int:
    """How many sections got their company."""
    filled, after = 0, None

    while batch := await read_batch(after):
        after = batch[-1][0]
        filled += await rounds.fill_session_companies(
            {set_id: company_id for _, set_id, company_id in batch}
        )

    return filled


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Sections given their company: %d", asyncio.run(backfill()))
