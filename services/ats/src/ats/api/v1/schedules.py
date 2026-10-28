from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from ats.services import outbox as outbox_service
from ats.services import recovery

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
    await recovery.run()
