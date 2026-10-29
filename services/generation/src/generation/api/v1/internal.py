from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.ai.ai_cap import refuse_if_capped
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from generation.api.dependencies import ServiceCaller
from generation.constants.actions import (
    CAMPAIGN_TRANSLATION,
    NEWS_TRANSLATION,
    QUESTION_REGENERATION,
    QUESTION_VERIFY,
)
from generation.constants.generation import (
    TRANSLATE_NEWS,
    VERIFY_QUESTION,
)
from generation.core.db import Session
from generation.helpers.questions import set_company
from generation.integrations import library, tasks
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run
from generation.models.generation import Generation
from generation.repositories import generations
from generation.schemas.campaigns import CampaignSource
from generation.schemas.generation import GenerationOut, InterviewGenerationCreate, ReviewRequest
from generation.schemas.regenerate import RegeneratedOut, RegenerateIn
from generation.schemas.statuses import GenerationIdsIn, GenerationStatusesOut, GenerationStatusOut
from generation.schemas.verify import VerifyIn
from generation.services import translation_jobs
from generation.services.budget import use_daily_budget, use_verify_budget
from generation.services.cancel import cancel_generation
from generation.services.regenerate import regenerate
from generation.services.retry import retry_generation
from generation.services.review import submit_review
from generation.services.starts import start_interview
from generation.services.topic_caps import generation_out

router = APIRouter(prefix="/internal", tags=["internal"])


async def get_company_generation(generation_id: UUID, company_id: UUID) -> Generation:
    async with Session() as session:
        generation = await generations.get(session, generation_id)

    if generation is None or generation.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generation not found")

    return generation


@router.post("/generations", status_code=status.HTTP_201_CREATED)
async def create_interview_generation(
    body: InterviewGenerationCreate, caller: ServiceCaller, request: Request
) -> GenerationOut:
    """A company's test; companies charges per candidate, so generating it is free."""
    return await generation_out(await start_interview(body))


@router.post("/generations/statuses")
async def generation_statuses(
    body: GenerationIdsIn, caller: ServiceCaller
) -> GenerationStatusesOut:
    """Notifications, for its reminders: the status of each of those generations that still
    exists, who started it and since when."""
    async with Session() as session:
        found = await generations.by_ids(session, body.ids)

    return GenerationStatusesOut(
        generations=[GenerationStatusOut.model_validate(row) for row in found]
    )


@router.get("/generations/{generation_id}")
async def get_interview_generation(
    generation_id: UUID, company_id: UUID, caller: ServiceCaller
) -> GenerationOut:
    """For a caller that already checked the user belongs to the company."""
    return await generation_out(await get_company_generation(generation_id, company_id))


@router.post("/generations/{generation_id}/review")
async def review_interview_generation(
    generation_id: UUID,
    company_id: UUID,
    body: ReviewRequest,
    caller: ServiceCaller,
    request: Request,
) -> GenerationOut:
    """For a caller that already checked the user may manage the company's interviews."""
    generation = await get_company_generation(generation_id, company_id)

    return await generation_out(await submit_review(generation, body))


@router.post("/generations/{generation_id}/retry")
async def retry_interview_generation(
    generation_id: UUID, company_id: UUID, caller: ServiceCaller, request: Request
) -> GenerationOut:
    """For a caller that already checked the user may manage the company's interviews."""
    generation = await get_company_generation(generation_id, company_id)

    return await generation_out(await retry_generation(generation))


@router.post("/generations/{generation_id}/cancel")
async def cancel_interview_generation(
    generation_id: UUID, company_id: UUID, caller: ServiceCaller
) -> GenerationOut:
    """For a caller that already checked the user may manage the company's interviews."""
    generation = await get_company_generation(generation_id, company_id)

    return await generation_out(await cancel_generation(generation))


@router.post("/questions/{question_id}/regenerate")
async def regenerate_interview_question(
    question_id: UUID, body: RegenerateIn, caller: ServiceCaller, request: Request
) -> RegeneratedOut:
    """For a caller that already checked the user may edit this set."""
    context = await library.get_question_context(question_id)

    if context is None or context.set_id != body.set_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    who = {"company_id": set_company(context), "user_id": body.user_id}

    if not body.paid:
        await refuse_if_capped(get_redis(), **who)

    await hit(get_redis(), f"rate:regenerations:{body.user_id}", "REGENERATION_LIMIT", **who)
    await use_daily_budget(body.paid, **who)

    async with ai_run(QUESTION_REGENERATION, subject_id=question_id, **who):
        question = await regenerate(question_id, context)

    if question is None:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Couldn't generate a new question")

    return question


@router.post("/questions/{question_id}/verify", status_code=status.HTTP_202_ACCEPTED)
async def verify_question(
    question_id: UUID, body: VerifyIn, caller: ServiceCaller, request: Request
) -> None:
    """The library flagged the question; the worker checks it and fixes or replaces it. Past
    the daily cap or while paused the call is refused, and the library sends the flag again
    later."""
    await refuse_if_paused(get_redis(), QUESTION_VERIFY)

    if not body.now:
        await use_verify_budget()

    await tasks.enqueue(
        VERIFY_QUESTION, {"question_id": str(question_id), "flag": body.flag, "now": body.now}
    )


@router.post("/news/{news_id}/translate", status_code=status.HTTP_202_ACCEPTED)
async def translate_news(news_id: UUID, caller: ServiceCaller) -> None:
    """The library saved a news post; the worker translates it into the languages it lacks.
    While paused the call is refused, and the library sends the post again later."""
    await refuse_if_paused(get_redis(), NEWS_TRANSLATION)
    await tasks.enqueue(TRANSLATE_NEWS, {"news_id": str(news_id)})


@router.post("/campaigns/{campaign_id}/translate", status_code=status.HTTP_202_ACCEPTED)
async def translate_campaign(
    campaign_id: UUID, body: CampaignSource, caller: ServiceCaller
) -> None:
    """Notifications saved a campaign, sending its English texts and the languages it lacks;
    each language is queued for the next batch, and the translations go back as
    `notification.campaign_translated`. While paused the call is refused, and saving the
    campaign again sends it again."""
    await refuse_if_paused(get_redis(), CAMPAIGN_TRANSLATION)
    await translation_jobs.translate_campaign(campaign_id, body)
