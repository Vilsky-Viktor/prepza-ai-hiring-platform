from fastapi import APIRouter, Request, status
from prepza_common.google import Invoker

from app.services import patterns, schedules

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/sweep", status_code=status.HTTP_204_NO_CONTENT)
async def sweep(request: Request) -> None:
    """Every 5 minutes: fails generations whose worker died, expires old reviews, deletes
    checkpoints nothing will resume."""
    await schedules.sweep(request.app.state.checkpointer)


@router.post("/key-check-batches", status_code=status.HTTP_204_NO_CONTENT)
async def key_check_batches() -> None:
    """Every 10 minutes: applies finished OpenAI batches of key checks, sends waiting ones."""
    await schedules.key_check_batches()


@router.post("/retention", status_code=status.HTTP_204_NO_CONTENT)
async def retention(request: Request) -> None:
    """Daily: pasted job texts aren't kept longer than needed."""
    await schedules.retention(request.app.state.checkpointer)


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute: publishes events that weren't published right after their change."""
    await schedules.flush_outbox()


@router.post("/patterns", status_code=status.HTTP_204_NO_CONTENT)
async def quality_patterns() -> None:
    """Weekly: the recurring mistakes in last week's flagged and replaced questions, proposed
    as general rules for a superadmin to review."""
    await patterns.run()
