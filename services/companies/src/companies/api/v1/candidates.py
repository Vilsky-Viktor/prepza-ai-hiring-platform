from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams

from companies.api.dependencies import Via
from companies.constants.invites import MAX_SEARCH_LENGTH, OPEN, CandidateFilter, CandidateSort
from companies.core.db import Session
from companies.helpers.candidates import row_actions
from companies.repositories import invites
from companies.schemas.invites import (
    CandidateFiltersOut,
    CandidateIn,
    CandidateNameIn,
    CandidateOut,
)
from companies.schemas.scorecards import ScorecardOut
from companies.services import candidate_changes, candidate_invites, candidate_results, scorecards
from companies.services import outbox as outbox_service
from companies.services.interview_access import candidate_for, interview_for, ready_for_invites

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/{interview_id}/candidates", status_code=status.HTTP_201_CREATED)
async def invite_candidate(
    interview_id: UUID, body: CandidateIn, user: CurrentUser, response: Response
) -> CandidateOut:
    """Invites the candidate (201), or sends an invite that's still open again (200: nothing
    new is made, as the public API answers); an expired one comes back to life (201)."""
    interview, company, _ = await interview_for(user, interview_id, editor=True)
    interview = await ready_for_invites(interview, user.uid)

    async with Session() as session:
        earlier, _ = await invites.held(session, interview.id, str(body.email))

    invite = await candidate_invites.invite(interview, company, user, str(body.email), body.name)
    await outbox_service.flush_quietly()

    if earlier in OPEN:
        response.status_code = status.HTTP_200_OK

    return CandidateOut(
        id=invite.id,
        email=invite.email,
        name=invite.name,
        status=invite.status,
        created_at=invite.created_at,
        **row_actions(invite.status),
    )


@router.get("/candidates/filters")
def candidate_filters() -> CandidateFiltersOut:
    """What candidates can be filtered by."""
    return CandidateFiltersOut(filters=list(CandidateFilter))


@router.get("/{interview_id}/candidates")
async def list_candidates(
    interview_id: UUID,
    user: CurrentUser,
    page: PageParams,
    sort: CandidateSort = CandidateSort.DATE,
    q: Annotated[str, Query(max_length=MAX_SEARCH_LENGTH)] = "",
    filter_by: Annotated[CandidateFilter | None, Query(alias="status")] = None,
) -> list[CandidateOut]:
    """A page at a time (candidate_results.page)."""
    interview, _, _ = await interview_for(user, interview_id)
    by_grade = sort == CandidateSort.GRADE

    return await candidate_results.page(
        interview, page.offset, page.limit, by_grade, q.strip(), filter_by
    )


@router.delete("/{interview_id}/candidates/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_candidate(
    interview_id: UUID, invite_id: UUID, user: CurrentUser, via: Via
) -> None:
    """Withdraws an invite not used yet, or erases a candidate who started (candidate_changes)."""
    interview, invite, _, _ = await candidate_for(user, interview_id, invite_id, editor=True)
    await candidate_changes.remove(interview, invite, user.uid, via)


@router.patch("/{interview_id}/candidates/{invite_id}/name", status_code=status.HTTP_204_NO_CONTENT)
async def rename_candidate(
    interview_id: UUID, invite_id: UUID, body: CandidateNameIn, user: CurrentUser
) -> None:
    """Owners and admins correct the name a candidate's sign-in gave, a nickname for example; a
    blank name makes it not known. The sign-in fills only a name not known, so this one stays."""
    interview, invite, _, _ = await candidate_for(user, interview_id, invite_id, editor=True)
    await candidate_changes.change(interview, invite, {"name": body.name or None}, user.uid)


@router.get("/{interview_id}/candidates/{invite_id}")
async def candidate_scorecard(
    interview_id: UUID,
    invite_id: UUID,
    user: CurrentUser,
    via: Via,
) -> ScorecardOut:
    """A view through the in-app assistant or an AI app (a valid X-Assistant token) is audited
    as via it and isn't the funnel's "results viewed"."""
    interview, invite, company, member = await candidate_for(user, interview_id, invite_id)

    return await scorecards.scorecard(interview, invite, company, member, user, via)
