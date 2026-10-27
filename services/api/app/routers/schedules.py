import logging

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from app.services import outbox as outbox_service
from app.services import webhooks

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/internal/schedules",
    tags=["schedules"],
    dependencies=[Invoker],
    include_in_schema=False,
)


@router.post("/webhook-retries", status_code=status.HTTP_204_NO_CONTENT)
async def retry_webhooks() -> None:
    """Every 5 minutes, from Cloud Scheduler: events web hooks didn't take are sent again."""
    due = await webhooks.retry()

    if due:
        logger.info("Sent %d events again to web hooks", due)


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()
