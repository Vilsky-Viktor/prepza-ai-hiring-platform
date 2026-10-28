"""One-off: gives rounds the company of every interview's sections started before rounds kept
it (migration rounds 0029), a batch of interviews at a time. Safe to run again.
Run: python -m companies.services.round_companies"""

import asyncio
import logging

from companies.constants.reports import READ_BATCH
from companies.integrations import rounds
from companies.repositories import interviews

logger = logging.getLogger(__name__)


async def backfill() -> int:
    """How many sections got their company."""
    filled, after = 0, None

    while batch := await interviews.set_companies(after, READ_BATCH):
        after = batch[-1][0]
        filled += await rounds.fill_session_companies(
            {set_id: company_id for _, set_id, company_id in batch}
        )

    return filled


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Sections given their company: %d", asyncio.run(backfill()))
