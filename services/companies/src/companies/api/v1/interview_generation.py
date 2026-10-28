from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.ai import ai_cap
from prepza_common.auth.auth import CurrentUser
from prepza_common.auth.human_check import require_human
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from companies.api.dependencies import Via
from companies.config import settings
from companies.constants.generation import GENERATION_REFUSALS
from companies.integrations import billing
from companies.integrations import generation as generation_api
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.repositories import audit, interview_generations, interviews
from companies.schemas.generations import GenerationOut
from companies.schemas.interviews import ReviewIn
from companies.services.interview_access import interview_for

router = APIRouter(prefix="/interviews", tags=["interviews"])


async def get_interview(user: CurrentUser, interview_id: UUID, editor: bool = False) -> Interview:
    """The user's interview (interview_for), only one with a generation to follow."""
    interview, _, _ = await interview_for(user, interview_id, editor)

    # A test made from a template has no generation to follow.
    if interview.generation_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    return interview


@router.get("/{interview_id}/generation")
async def get_generation(interview_id: UUID, user: CurrentUser) -> GenerationOut:
    """Every company member follows the generation, not only the admin who started it."""
    interview = await get_interview(user, interview_id)
    found = await generation_api.get(interview.generation_id, interview.company_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generation not found")

    return found


@router.post("/{interview_id}/generation/review")
async def review_generation(
    interview_id: UUID, body: ReviewIn, user: CurrentUser, via: Via, request: Request
) -> dict:
    """Approved topics resume the generation, so a pause refuses it. A company that never paid
    shows it's a person on the site first, as generating costs (the assistant and AI apps, with
    no browser, can't be asked), and is refused once today's unpaid AI spend reached its cap."""
    interview = await get_interview(user, interview_id, editor=True)
    company_id = interview.company_id
    await refuse_if_paused(get_redis(), "interview_generation", company_id, user.uid)

    if not await billing.company_paid(company_id):
        if via is None and settings.turnstile_secret_key:
            await require_human(request, settings.turnstile_secret_key)

        await ai_cap.refuse_if_capped(get_redis(), company_id, user.uid)

    response = await generation_api.review(
        interview.generation_id, interview.company_id, body.model_dump()
    )
    reviewed = passed_on(response, GENERATION_REFUSALS).json()
    await audit.record_interview(interview, user.uid, AuditAction.TOPICS_APPROVED, via)

    return reviewed


@router.post("/{interview_id}/generation/retry")
async def retry_generation(interview_id: UUID, user: CurrentUser) -> dict:
    """Runs the generation again, so it's refused as a review is (without the person check)."""
    interview = await get_interview(user, interview_id, editor=True)
    await refuse_if_paused(get_redis(), "interview_generation", interview.company_id, user.uid)

    if not await billing.company_paid(interview.company_id):
        await ai_cap.refuse_if_capped(get_redis(), interview.company_id, user.uid)

    # A run again is AI work as the first was.
    key = f"rate:generation-retries:{interview.company_id}"
    company_id = interview.company_id
    await hit(get_redis(), key, "GENERATION_RETRIES_PER_COMPANY_DAY", company_id=company_id)
    retried = passed_on(
        await generation_api.retry(interview.generation_id, interview.company_id),
        GENERATION_REFUSALS,
    ).json()
    # Generating again: its lists stop showing the failure.
    await interview_generations.set_generation_failed(interview.id, False)

    return retried


@router.post("/{interview_id}/generation/cancel")
async def cancel_generation(interview_id: UUID, user: CurrentUser) -> dict:
    """Removes the interview too, so it isn't left without questions."""
    interview = await get_interview(user, interview_id, editor=True)
    cancelled = passed_on(
        await generation_api.cancel(interview.generation_id, interview.company_id),
        GENERATION_REFUSALS,
    ).json()
    await interviews.remove(interview.id)

    return cancelled
