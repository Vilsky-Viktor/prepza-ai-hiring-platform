"""Starting a generation: a company's test, a superadmin's template or questions added to a
template. The limits, the budget and the text check (Redis, a model) run first; the queued row
is saved in its own transaction, and its job is queued once it's committed."""

from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.ai.ai_cap import refuse_if_capped
from prepza_common.i18n.text_language import text_language
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit
from sqlalchemy.exc import IntegrityError

from generation.constants.actions import INTERVIEW_GENERATION, TEMPLATE_GENERATION
from generation.constants.additions import ADDITION_RUNNING, NOTHING_TO_TOP_UP
from generation.constants.generation import RUN_GENERATION
from generation.constants.kinds import GenerationKind
from generation.core.db import Session
from generation.helpers.additions import planned
from generation.integrations import library, tasks
from generation.integrations.redis import get_redis
from generation.models.generation import Generation
from generation.repositories import generations
from generation.schemas.generation import InterviewGenerationCreate, TemplateGenerationCreate
from generation.services.budget import use_daily_budget
from generation.services.screen import refuse_if_nothing_to_test


async def queued(generation: Generation) -> Generation:
    await tasks.enqueue(RUN_GENERATION, {"generation_id": str(generation.id)})

    return generation


async def start_interview(body: InterviewGenerationCreate) -> Generation:
    """A company's test; companies charges per candidate, so generating it is free."""
    who = {"company_id": body.company_id, "user_id": body.owner_uid}

    if not body.paid:
        await refuse_if_capped(get_redis(), **who)

    await hit(get_redis(), f"rate:generations:{body.owner_uid}", "GENERATION_LIMIT", **who)
    await use_daily_budget(body.paid, **who)
    await refuse_if_nothing_to_test(body.text, INTERVIEW_GENERATION, **who)
    language = body.generate_in or text_language(body.text, body.language)

    async with Session.begin() as session:
        generation = await generations.create(
            session, body.owner_uid, body.text, body.company_id, language
        )

    return await queued(generation)


async def start_template(
    body: TemplateGenerationCreate, user_id: str, interface_language: str
) -> Generation:
    """A superadmin's template: the same pipeline, saved without a company."""
    await refuse_if_paused(get_redis(), TEMPLATE_GENERATION, user_id=user_id)
    await use_daily_budget(user_id=user_id)
    await refuse_if_nothing_to_test(body.text, TEMPLATE_GENERATION, user_id=user_id)
    language = body.generate_in or text_language(body.text, interface_language)

    async with Session.begin() as session:
        generation = await generations.create(
            session, user_id, body.text, language=language, kind=GenerationKind.TEMPLATE
        )

    return await queued(generation)


async def start_addition(template_id: UUID, owner_uid: str, count: int | None) -> Generation:
    """Queues an addition of `count` questions to every topic, or a top-up without one."""
    await refuse_if_paused(get_redis(), TEMPLATE_GENERATION, user_id=owner_uid)
    context = await library.get_addition_context(template_id)

    if context is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    if not any(sum(planned(topic, count)) for topic in context.topics):
        raise HTTPException(status.HTTP_409_CONFLICT, NOTHING_TO_TOP_UP)

    await use_daily_budget(user_id=owner_uid)

    try:
        async with Session.begin() as session:
            generation = await generations.create_addition(
                session, owner_uid, template_id, context.language, count
            )
    except IntegrityError:
        # Another addition to this template is queued or running.
        raise HTTPException(status.HTTP_409_CONFLICT, ADDITION_RUNNING) from None

    return await queued(generation)
