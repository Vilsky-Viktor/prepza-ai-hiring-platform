from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from site_content.services import outbox as outbox_service

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change, and deletes those published a week ago."""
    await outbox_service.flush()
