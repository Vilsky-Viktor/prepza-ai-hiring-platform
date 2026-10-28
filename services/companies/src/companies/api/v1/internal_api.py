import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.db.paging import PageParams

from companies.api.dependencies import ServiceCaller
from companies.helpers.candidates import candidate_out
from companies.helpers.interviews import attach_set_if_reachable, interview_out
from companies.integrations import rounds
from companies.repositories import candidates, interviews
from companies.schemas.interviews import InterviewOut
from companies.schemas.invites import CandidateOut, SectionGrade
from companies.services import candidate_results

router = APIRouter(prefix="/internal/companies/{company_id}/interviews", tags=["internal"])


async def company_interview(company_id: UUID, interview_id: UUID):
    """The interview, if it's the company's; 404 otherwise, as if it weren't there."""
    interview = await interviews.get(interview_id)

    if interview is None or interview.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    return interview


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
    rows = await interviews.list_for_company(
        company_id, page.offset, page.limit, updated_since, after
    )
    totals = await candidates.counts([item.id for item in rows])

    return [await interview_out(item, totals.get(item.id, 0)) for item in rows]


@router.get("/{interview_id}")
async def get_interview(
    company_id: UUID, interview_id: UUID, caller: ServiceCaller
) -> InterviewOut:
    interview = await attach_set_if_reachable(await company_interview(company_id, interview_id))
    totals = await candidates.counts([interview.id])

    return await interview_out(interview, totals.get(interview.id, 0))


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
    interview = await company_interview(company_id, interview_id)

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
    interview = await company_interview(company_id, interview_id)
    invite = await candidates.get(interview.id, invite_id)

    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    # Both from rounds, asked at once.
    totals, card = await asyncio.gather(
        rounds.invite_scores([invite.id]), rounds.scorecard(invite.id)
    )
    found = candidate_out(invite, totals.get(str(invite.id)) or {}, interview, with_link=True)
    found.sections = [
        SectionGrade(title=section["topic_title"], grade=section["final_score"])
        for section in card or []
    ]

    return found
