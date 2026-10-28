import asyncio
import logging
import uuid

from generation.constants.generation import (
    GENERATION_FAILED,
    GENERATION_STOPPED,
    JOB_TIMEOUT_SECONDS,
)
from generation.constants.kinds import GenerationKind
from generation.constants.statuses import Status
from generation.core.db import Session
from generation.helpers.events import failed_event
from generation.repositories import generations
from generation.services import outbox as outbox_service
from generation.services import run_state
from generation.services.additions import run_addition
from generation.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)


async def run_generation(graph, generation_id: uuid.UUID, resume: dict | None) -> None:
    """Runs one generation to its end or its review. Never raises: a failure is saved on the
    generation, which the user can retry, so Cloud Tasks never runs it twice; the event saved
    with it tells companies."""
    # Only a queued generation runs, and only once: not one cancelled while it waited, failed
    # by the sweeper, or already claimed by another delivery of this job.
    async with Session.begin() as session:
        if not await generations.claim_run(session, generation_id):
            return

        generation = await generations.get(session, generation_id)

    if generation is None:
        return

    # Questions added to a template have no topics to draft or review: no graph.
    if generation.kind == GenerationKind.TEMPLATE_QUESTIONS:
        run = run_addition(generation)
    else:
        run = run_pipeline(graph, generation, resume)

    try:
        await asyncio.wait_for(run, JOB_TIMEOUT_SECONDS)
    except TimeoutError:
        logger.error("Generation %s ran out of time", generation_id)
        error = GENERATION_STOPPED
    except Exception:
        logger.exception("Generation %s failed", generation_id)
        error = GENERATION_FAILED
    else:
        return

    await run_state.save(generation_id, failed_event(generation), status=Status.FAILED, error=error)
    await outbox_service.flush_quietly()
