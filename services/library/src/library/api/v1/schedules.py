from fastapi import APIRouter, status
from testee_common.auth.google import Invoker

from library.services import housekeeping
from library.services import outbox as outbox_service

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/bank", status_code=status.HTTP_204_NO_CONTENT)
async def daily_housekeeping() -> None:
    """Daily, from Cloud Scheduler: sends flags the verifier hasn't acted on to it again, takes
    out of the shared bank what a flag, report or opt-out raced, and forgets old notes of
    processed events."""
    await housekeeping.daily()
