from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from testee_common.auth.auth import CurrentUser

from companies.api.dependencies import Via
from companies.integrations import generation as generation_api
from companies.models.interviews import Interview
from companies.schemas.generations import GenerationOut
from companies.schemas.interviews import ReviewIn
from companies.services import generation_steps, interview_removal
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

    return await generation_steps.review(interview, body.model_dump(), user.uid, via, request)


@router.post("/{interview_id}/generation/retry")
async def retry_generation(interview_id: UUID, user: CurrentUser) -> dict:
    """Runs the generation again, so it's refused as a review is (without the person check)."""
    interview = await get_interview(user, interview_id, editor=True)

    return await generation_steps.retry(interview, user.uid)


@router.post("/{interview_id}/generation/cancel")
async def cancel_generation(interview_id: UUID, user: CurrentUser) -> dict:
    """Removes the interview too, so it isn't left without questions."""
    interview = await get_interview(user, interview_id, editor=True)

    return await interview_removal.cancel_generation(interview)
