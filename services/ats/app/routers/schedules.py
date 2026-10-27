import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from app.constants.ats import CANDIDATE_RETENTION_DAYS
from app.services import ats_candidates
from app.services import outbox as outbox_service
from app.storage import ats_candidates as candidates_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/recover", status_code=status.HTTP_204_NO_CONTENT)
async def recover() -> None:
    """Every 10 minutes, from Cloud Scheduler: waiting candidates and invites cut off midway are
    invited (companies refuses them during the emergency pause, and they're kept to retry),
    results kept while a connection was broken or the ATS failed go back, and candidates past
    their retention period go."""
    recovered = await ats_candidates.recover()

    if recovered:
        logger.info("Found %d ATS candidates waiting or cut off midway", recovered)

    before = datetime.now(UTC) - timedelta(days=CANDIDATE_RETENTION_DAYS)
    deleted = await candidates_storage.delete_older_than(before)

    if deleted:
        logger.info("Deleted %d ATS candidates past their retention period", deleted)
