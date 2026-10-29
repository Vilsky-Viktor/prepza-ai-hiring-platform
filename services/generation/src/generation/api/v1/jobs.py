from fastapi import APIRouter, Request, status
from prepza_common.auth.google import Invoker

from generation.schemas.jobs import RunGeneration, VerifyQuestion
from generation.services.jobs import run_generation
from generation.services.verify import verify

router = APIRouter(prefix="/internal/jobs", tags=["jobs"], dependencies=[Invoker])


@router.post("/run-generation", status_code=status.HTTP_204_NO_CONTENT)
async def run_generation_job(body: RunGeneration, request: Request) -> None:
    """One Cloud Task: the whole generation, or up to its topic review."""
    await run_generation(request.app.state.graph, body.generation_id, body.resume)


@router.post("/verify-question", status_code=status.HTTP_204_NO_CONTENT)
async def verify_question_job(body: VerifyQuestion) -> None:
    await verify(body.question_id, body.flag, body.now)
