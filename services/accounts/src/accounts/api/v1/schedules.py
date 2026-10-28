import logging

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from accounts.services import erasures

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/erasures", status_code=status.HTTP_204_NO_CONTENT)
async def replay_erasures() -> None:
    """Daily, from Cloud Scheduler, and by hand right after a database restore or clone: the
    accounts deleted in the backups' life are deleted again everywhere (safe to repeat)."""
    count = await erasures.replay()
    logger.info("Ran %d recent account deletions again", count)
