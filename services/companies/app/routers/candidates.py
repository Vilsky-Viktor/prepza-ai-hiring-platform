import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from prepza_common.analytics import track
from prepza_common.auth import CurrentUser
from prepza_common.paging import PageParams

from app.constants.invites import (
    EXTRA_TIME_OPTIONS,
    MAX_SEARCH_LENGTH,
    NOT_STARTED,
    CandidateFilter,
    CandidateSort,
    InviteStatus,
)
from app.helpers.candidates import open_link_token, passed, row_actions, section_passed
from app.helpers.interviews import (
    interview_title,
)
from app.helpers.logos import logo_path
from app.integrations import rounds
from app.schemas.invites import CandidateFiltersOut, CandidateIn, CandidateNameIn, CandidateOut
from app.schemas.scorecards import ScorecardOut
from app.service_auth import Via
from app.services import candidate_changes, candidate_invites, candidate_results
from app.services import outbox as outbox_service
from app.services.access import can_edit
from app.services.interview_access import candidate_for, interview_for, ready_for_invites
from app.storage import audit

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/{interview_id}/candidates", status_code=status.HTTP_201_CREATED)
async def invite_candidate(
    interview_id: UUID, body: CandidateIn, user: CurrentUser
) -> CandidateOut:
    interview, company, _ = await interview_for(user, interview_id, editor=True)
    interview = await ready_for_invites(interview, user.uid)

    invite = await candidate_invites.invite(interview, company, user, str(body.email), body.name)
    await outbox_service.flush_quietly()

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
    await candidate_changes.rename(interview, invite, body.name, user.uid)


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
    # Both from rounds, asked at once.
    card, scores = await asyncio.gather(
        rounds.scorecard(invite.id), rounds.invite_scores([invite.id])
    )
    card = card or []
    totals = scores.get(str(invite.id)) or {}
    await candidate_results.sync([invite], {str(invite.id): totals})

    # The funnel's "first results viewed": a finished candidate's results, opened by a member
    # (not through the assistant or an AI app). The audit row is written whatever happens to the
    # funnel event, which never raises.
    if invite.status == InviteStatus.FINISHED and via is not None:
        await audit.record_view(company.id, user.uid, invite.id, via)
    elif invite.status == InviteStatus.FINISHED:
        await asyncio.gather(
            track("results_viewed", user_id=user.uid, company_id=company.id),
            audit.record_view(company.id, user.uid, invite.id),
        )

    return ScorecardOut(
        id=invite.id,
        email=invite.email,
        name=invite.name,
        status=invite.status,
        extra_time=invite.extra_time,
        can_edit=can_edit(member),
        **row_actions(invite.status),
        extra_time_options=(
            list(EXTRA_TIME_OPTIONS) if invite.status in NOT_STARTED and can_edit(member) else []
        ),
        invite_token=open_link_token(invite) if can_edit(member) else None,
        title=await interview_title(interview),
        company=company.name,
        logo_url=logo_path(company),
        verified_domain=company.verified_domain,
        grade=totals.get("grade"),
        passed=passed(totals, interview.pass_mark),
        pass_mark=interview.pass_mark,
        pledged_at=invite.pledged_at,
        sessions=[
            {**section, "passed": section_passed(section, interview.pass_mark)} for section in card
        ],
    )
