import logging
import time
from datetime import UTC, datetime, timedelta

from ats.constants.ats import CANDIDATE_RETENTION_DAYS, RECOVER_INVITE_SECONDS, REPORT_SECONDS
from ats.core.db import Session
from ats.repositories import ats_candidates, ats_results
from ats.services.ats_candidates import invite_all
from ats.services.reports import report

logger = logging.getLogger(__name__)


async def recover() -> int:
    """Every 10 minutes: candidates still waiting (left for later by a run, by companies not
    answering, or sent while the connection was broken) and invites cut off midway (the server
    stopped) are invited, until RECOVER_INVITE_SECONDS into the run; results kept while a
    connection was broken or the ATS failed go back, until REPORT_SECONDS into it. Both go
    through every connection's in turn. How many candidates were found."""
    started = time.monotonic()

    async with Session() as session:
        rows = await ats_candidates.recoverable(session)

    await invite_all(rows, started + RECOVER_INVITE_SECONDS)

    async with Session() as session:
        kept = await ats_results.unreported(session)

    for row in kept:
        if time.monotonic() >= started + REPORT_SECONDS:
            break

        try:
            await report(row.result)
        except Exception:
            logger.exception("Couldn't send the results of ATS candidate %s", row.id)

    return len(rows)


async def run() -> None:
    """The recovery job (recover), then candidates past their retention period go."""
    recovered = await recover()

    if recovered:
        logger.info("Found %d ATS candidates waiting or cut off midway", recovered)

    before = datetime.now(UTC) - timedelta(days=CANDIDATE_RETENTION_DAYS)
    deleted = await ats_candidates.delete_older_than(Session, before)

    if deleted:
        logger.info("Deleted %d ATS candidates past their retention period", deleted)
