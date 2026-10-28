from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.limits.limit_schemas import BudgetOut
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from generation.constants.actions import TEMPLATE_GENERATION, TEMPLATE_QUESTION_REGENERATION
from generation.constants.kinds import GenerationKind
from generation.core.db import Session
from generation.integrations import library
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run
from generation.models.generation import Generation
from generation.repositories import generations
from generation.schemas.generation import GenerationOut, ReviewRequest, TemplateGenerationCreate
from generation.schemas.regenerate import RegeneratedOut
from generation.services.budget import budgets
from generation.services.cancel import cancel_generation
from generation.services.regenerate import regenerate
from generation.services.retry import retry_generation
from generation.services.review import submit_review
from generation.services.starts import start_template
from generation.services.topic_caps import generation_out

# The superadmin's templates (docs/features/admin-zone.md, Templates): the same pipeline as a company's test,
# saved without a company. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


async def get_template_generation(generation_id: UUID) -> Generation:
    async with Session() as session:
        generation = await generations.get(session, generation_id)

    if generation is None or generation.kind != GenerationKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generation not found")

    return generation


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateGenerationCreate, superadmin: SuperadminUser
) -> GenerationOut:
    generation = await start_template(body, superadmin.uid, superadmin.language)

    return await generation_out(generation)


@router.get("/generations/{generation_id}")
async def get_generation(generation_id: UUID, superadmin: SuperadminUser) -> GenerationOut:
    return await generation_out(await get_template_generation(generation_id))


@router.post("/generations/{generation_id}/review")
async def review_generation(
    generation_id: UUID, body: ReviewRequest, superadmin: SuperadminUser
) -> GenerationOut:
    await refuse_if_paused(get_redis(), TEMPLATE_GENERATION, user_id=superadmin.uid)
    generation = await get_template_generation(generation_id)

    return await generation_out(await submit_review(generation, body))


@router.post("/generations/{generation_id}/retry")
async def retry(generation_id: UUID, superadmin: SuperadminUser) -> GenerationOut:
    await refuse_if_paused(get_redis(), TEMPLATE_GENERATION, user_id=superadmin.uid)
    generation = await get_template_generation(generation_id)

    return await generation_out(await retry_generation(generation))


@router.post("/generations/{generation_id}/cancel")
async def cancel(generation_id: UUID, superadmin: SuperadminUser) -> GenerationOut:
    generation = await get_template_generation(generation_id)

    return await generation_out(await cancel_generation(generation))


@router.post("/templates/{template_id}/questions/{question_id}/regenerate")
async def regenerate_question(
    template_id: UUID, question_id: UUID, superadmin: SuperadminUser
) -> RegeneratedOut:
    await refuse_if_paused(get_redis(), TEMPLATE_QUESTION_REGENERATION, user_id=superadmin.uid)
    context = await library.get_question_context(question_id)

    if context is None or context.set_id != template_id or context.kind != "template":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    key = f"rate:regenerations:{superadmin.uid}"
    await hit(get_redis(), key, "REGENERATION_LIMIT", user_id=superadmin.uid)

    async with ai_run(
        TEMPLATE_QUESTION_REGENERATION, user_id=superadmin.uid, subject_id=question_id
    ):
        question = await regenerate(question_id, context)

    if question is None:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Couldn't generate a new question")

    return question


@router.get("/budgets")
async def get_budgets(superadmin: SuperadminUser) -> list[BudgetOut]:
    """How much of generation's shared daily budgets is used today (the AI costs tab)."""
    return await budgets()
