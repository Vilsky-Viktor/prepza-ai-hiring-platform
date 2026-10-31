from fastapi import APIRouter, status
from testee_common.auth.google import Invoker

from assistant.integrations import trace_retention
from assistant.services import retention as retention_service

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/traces", status_code=status.HTTP_204_NO_CONTENT)
async def trace_retention_job() -> None:
    """Daily, from Cloud Scheduler: every service's Langfuse traces a day short of their 30 days
    go (Langfuse's free plan has no retention of its own). Nothing without Langfuse."""
    await trace_retention.delete_old_traces()


@router.post("/retention", status_code=status.HTTP_204_NO_CONTENT)
async def retention() -> None:
    """Daily, from Cloud Scheduler: conversations nobody added to for ASSISTANT_RETENTION_DAYS
    go, with their messages and tool calls, a batch at a time until none are left; so do AI
    apps' connections whose refresh token expired, apps with no connection that registered over
    IDLE_CLIENT_DAYS ago, and get_updates checks no connection or key made in KEEP_DAYS. Safe to
    run twice at once or again: each deletes what's still there."""
    await retention_service.delete_old()
