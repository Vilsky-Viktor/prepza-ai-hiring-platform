import asyncio

from prepza_common.auth.user import User
from prepza_common.events.analytics import track

from companies.constants.invites import EXTRA_TIME_OPTIONS, NOT_STARTED, InviteStatus
from companies.core.db import Session
from companies.helpers.candidates import open_link_token, passed, row_actions, section_passed
from companies.helpers.logos import logo_path
from companies.integrations import rounds
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import audit
from companies.schemas.scorecards import ScorecardOut
from companies.services import candidate_results
from companies.services.access import can_edit
from companies.services.interview_views import interview_title


async def record_view(company_id, user_id: str, invite_id, via: str | None = None) -> None:
    async with Session.begin() as session:
        await audit.record_view(session, company_id, user_id, invite_id, via)


async def scorecard(
    interview: Interview,
    invite: CandidateInvite,
    company: Company,
    member: Member,
    user: User,
    via: str | None,
) -> ScorecardOut:
    """A candidate's results as their page shows them. A finished candidate's view is recorded
    in the action log; through the in-app assistant or an AI app it's recorded as via it and
    isn't the funnel's "results viewed"."""
    # All from rounds, asked at once.
    card, scores, patterns = await asyncio.gather(
        rounds.scorecard(invite.id),
        rounds.invite_scores([invite.id]),
        rounds.answer_patterns(invite.id),
    )
    card = card or []
    totals = scores.get(str(invite.id)) or {}
    await candidate_results.sync([invite], {str(invite.id): totals})

    # The funnel's "first results viewed": a finished candidate's results, opened by a member
    # (not through the assistant or an AI app). The audit row is written whatever happens to the
    # funnel event, which never raises.
    if invite.status == InviteStatus.FINISHED and via is not None:
        await record_view(company.id, user.uid, invite.id, via)
    elif invite.status == InviteStatus.FINISHED:
        await asyncio.gather(
            track("results_viewed", user_id=user.uid, company_id=company.id),
            record_view(company.id, user.uid, invite.id),
        )

    editor = can_edit(member)

    return ScorecardOut(
        id=invite.id,
        email=invite.email,
        name=invite.name,
        status=invite.status,
        extra_time=invite.extra_time,
        can_edit=editor,
        **row_actions(invite.status),
        extra_time_options=(
            list(EXTRA_TIME_OPTIONS) if invite.status in NOT_STARTED and editor else []
        ),
        invite_token=open_link_token(invite) if editor else None,
        title=await interview_title(interview),
        company=company.name,
        logo_url=logo_path(company),
        verified_domain=company.verified_domain,
        grade=totals.get("grade"),
        passed=passed(totals, interview.pass_mark),
        pass_mark=interview.pass_mark,
        language=interview.language,
        pledged_at=invite.pledged_at,
        sessions=[
            {**section, "passed": section_passed(section, interview.pass_mark)} for section in card
        ],
        answer_patterns=patterns or {},
    )
