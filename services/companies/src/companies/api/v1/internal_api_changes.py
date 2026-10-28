from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.config.constants import MAX_PAGE_SIZE

from companies.api.dependencies import ServiceCaller
from companies.constants.audit import VIA_API
from companies.core.db import Session
from companies.repositories import candidates
from companies.schemas.companies import CompanyCreditsOut
from companies.schemas.interviews import InterviewCreate, InterviewOut
from companies.schemas.invites import CandidateChangesIn, CandidateSearchIn, CompanyCandidateOut
from companies.services import (
    candidate_changes,
    candidate_invites,
    candidate_results,
    credits,
    interview_creation,
)
from companies.services.interview_views import company_interview

# What an API key changes, as `user_id`, the owner or admin who made it (the api service
# checked they still are), and finds by email.
router = APIRouter(prefix="/internal/companies/{company_id}", tags=["internal"])


async def company_candidate(company_id: UUID, interview_id: UUID, invite_id: UUID):
    interview = await company_interview(company_id, interview_id)

    async with Session() as session:
        invite = await candidates.get(session, interview.id, invite_id)

    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    return interview, invite


@router.post("/interviews", status_code=status.HTTP_201_CREATED)
async def create_interview(
    company_id: UUID, body: InterviewCreate, user_id: str, caller: ServiceCaller
) -> InterviewOut:
    return await interview_creation.create_for_api(company_id, user_id, body.text, body.generate_in)


@router.delete(
    "/interviews/{interview_id}/candidates/{invite_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_candidate(
    company_id: UUID, interview_id: UUID, invite_id: UUID, user_id: str, caller: ServiceCaller
) -> None:
    interview, invite = await company_candidate(company_id, interview_id, invite_id)
    await candidate_changes.remove(interview, invite, user_id, VIA_API)


@router.patch(
    "/interviews/{interview_id}/candidates/{invite_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def change_candidate(
    company_id: UUID,
    interview_id: UUID,
    invite_id: UUID,
    body: CandidateChangesIn,
    user_id: str,
    caller: ServiceCaller,
) -> None:
    """The candidate's name and extra time, as the body gives them, all or none (a blank name
    makes it not known)."""
    interview, invite = await company_candidate(company_id, interview_id, invite_id)
    changes = body.model_dump(exclude_unset=True)

    if "name" in changes:
        changes["name"] = changes["name"] or None

    await candidate_changes.change(interview, invite, changes, user_id, VIA_API)


@router.post(
    "/interviews/{interview_id}/candidates/{invite_id}/resend",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def resend_invite(
    company_id: UUID, interview_id: UUID, invite_id: UUID, user_id: str, caller: ServiceCaller
) -> None:
    """Sends the invite again, as an owner or admin does on the candidate's page: refused for a
    candidate who finished (409) or one prepza doesn't email (invited without a sign-in, 409);
    the invite keeps its return address and theme."""
    interview, invite = await company_candidate(company_id, interview_id, invite_id)
    await candidate_invites.resend(company_id, interview, invite, user_id)


@router.post("/candidates/search")
async def find_candidates(
    company_id: UUID, body: CandidateSearchIn, caller: ServiceCaller
) -> list[CompanyCandidateOut]:
    """The company's candidates invited with this email (in the body, out of URLs and their
    logs), in any of its interviews, newest first, with their results and invite links: at most
    a page, in one answer."""
    return await candidate_results.company_page(
        company_id, 0, MAX_PAGE_SIZE, email=str(body.email), with_link=True
    )


@router.get("/credits")
async def get_credits(company_id: UUID, caller: ServiceCaller) -> CompanyCreditsOut:
    return await credits.credits_of(company_id)
