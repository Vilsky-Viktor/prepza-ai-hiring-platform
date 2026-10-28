from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from prepza_common.db.paging import PageParams

from companies.api.dependencies import ServiceCaller
from companies.schemas.interviews import InterviewOut
from companies.schemas.invites import CandidateOut
from companies.services import candidate_results, interview_views

router = APIRouter(prefix="/internal/companies/{company_id}/interviews", tags=["internal"])


@router.get("")
async def list_interviews(
    company_id: UUID,
    page: PageParams,
    caller: ServiceCaller,
    updated_since: datetime | None = None,
    after: UUID | None = None,
) -> list[InterviewOut]:
    """The company's interviews, newest first, for the api service (an API key's company); with
    `updated_since`, those changed since, oldest change first."""
    return await interview_views.company_interviews(
        company_id, page.offset, page.limit, updated_since, after
    )


@router.get("/{interview_id}")
async def get_interview(
    company_id: UUID, interview_id: UUID, caller: ServiceCaller
) -> InterviewOut:
    interview = await interview_views.company_interview(company_id, interview_id)

    return await interview_views.one_out(await interview_views.attach_set_if_reachable(interview))


@router.get("/{interview_id}/candidates")
async def list_candidates(
    company_id: UUID,
    interview_id: UUID,
    page: PageParams,
    caller: ServiceCaller,
    updated_since: datetime | None = None,
    after: UUID | None = None,
) -> list[CandidateOut]:
    """The interview's candidates, newest first, with their results and invite links; with
    `updated_since`, those changed since, oldest change first."""
    interview = await interview_views.company_interview(company_id, interview_id)

    return await candidate_results.page(
        interview,
        page.offset,
        page.limit,
        by_grade=False,
        with_link=True,
        since=updated_since,
        after=after,
    )


@router.get("/{interview_id}/candidates/{invite_id}")
async def get_candidate(
    company_id: UUID, interview_id: UUID, invite_id: UUID, caller: ServiceCaller
) -> CandidateOut:
    interview = await interview_views.company_interview(company_id, interview_id)

    return await candidate_results.one(interview, invite_id)
