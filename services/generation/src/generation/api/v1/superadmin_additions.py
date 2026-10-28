from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.superadmin import SuperadminUser

from generation.core.db import Session
from generation.repositories import generations
from generation.schemas.additions import AdditionCreate, AdditionOut
from generation.services.starts import start_addition

# Adding questions to a superadmin's template (docs/features/admin-zone.md, Templates): a top-up
# writes what each topic lacks of its practice and company questions, an addition a number for
# every topic. Both run as a background job (services/additions.py), one at a time a template.
router = APIRouter(prefix="/superadmin/templates", tags=["superadmin"])


@router.get("/{template_id}/additions/latest")
async def latest_addition(template_id: UUID, superadmin: SuperadminUser) -> AdditionOut:
    async with Session() as session:
        generation = await generations.latest_addition(session, template_id)

    return AdditionOut.model_validate(generation) if generation else AdditionOut()


@router.post("/{template_id}/top-up", status_code=status.HTTP_201_CREATED)
async def top_up(template_id: UUID, superadmin: SuperadminUser) -> AdditionOut:
    return AdditionOut.model_validate(await start_addition(template_id, superadmin.uid, None))


@router.post("/{template_id}/additions", status_code=status.HTTP_201_CREATED)
async def add_questions(
    template_id: UUID, body: AdditionCreate, superadmin: SuperadminUser
) -> AdditionOut:
    generation = await start_addition(template_id, superadmin.uid, body.count)

    return AdditionOut.model_validate(generation)
