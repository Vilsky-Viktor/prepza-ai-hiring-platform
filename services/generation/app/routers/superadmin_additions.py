from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.limits.pause import refuse_if_paused

from app.constants.actions import TEMPLATE_GENERATION
from app.constants.additions import ADDITION_RUNNING, NOTHING_TO_TOP_UP
from app.constants.generation import RUN_GENERATION
from app.helpers.additions import planned
from app.integrations import library, tasks
from app.integrations.redis import get_redis
from app.schemas.additions import AdditionCreate, AdditionOut
from app.services.budget import use_daily_budget
from app.storage import generations

# Adding questions to a superadmin's template (docs/features/admin-zone.md, Templates): a top-up
# writes what each topic lacks of its practice and company questions, an addition a number for
# every topic. Both run as a background job (services/additions.py), one at a time a template.
router = APIRouter(prefix="/superadmin/templates", tags=["superadmin"])


@router.get("/{template_id}/additions/latest")
async def latest_addition(template_id: UUID, superadmin: SuperadminUser) -> AdditionOut:
    generation = await generations.latest_addition(template_id)

    return AdditionOut.model_validate(generation) if generation else AdditionOut()


@router.post("/{template_id}/top-up", status_code=status.HTTP_201_CREATED)
async def top_up(template_id: UUID, superadmin: SuperadminUser) -> AdditionOut:
    return await start(template_id, superadmin.uid, None)


@router.post("/{template_id}/additions", status_code=status.HTTP_201_CREATED)
async def add_questions(
    template_id: UUID, body: AdditionCreate, superadmin: SuperadminUser
) -> AdditionOut:
    return await start(template_id, superadmin.uid, body.count)


async def start(template_id: UUID, owner_uid: str, count: int | None) -> AdditionOut:
    """Queues an addition of `count` questions to every topic, or a top-up without one."""
    await refuse_if_paused(get_redis(), TEMPLATE_GENERATION, user_id=owner_uid)
    context = await library.get_addition_context(template_id)

    if context is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    if not any(sum(planned(topic, count)) for topic in context.topics):
        raise HTTPException(status.HTTP_409_CONFLICT, NOTHING_TO_TOP_UP)

    await use_daily_budget(user_id=owner_uid)
    generation = await generations.create_addition(owner_uid, template_id, context.language, count)

    if generation is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ADDITION_RUNNING)

    await tasks.enqueue(RUN_GENERATION, {"generation_id": str(generation.id)})

    return AdditionOut.model_validate(generation)
