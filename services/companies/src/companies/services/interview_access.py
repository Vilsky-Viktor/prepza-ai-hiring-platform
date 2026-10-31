from uuid import UUID

from fastapi import HTTPException, status
from testee_common.auth.auth import CurrentUser
from testee_common.limits.pause import refuse_if_paused

from companies.constants.invites import INTERVIEW_NOT_READY
from companies.core.db import Session
from companies.integrations.redis import get_redis
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, interviews
from companies.services.access import require_company, require_editor
from companies.services.interview_views import attach_set


async def interview_for(
    user: CurrentUser, interview_id: UUID, editor: bool = False
) -> tuple[Interview, Company, Member]:
    """The interview, when the user is a member of its company (with `editor`, an owner or
    admin of a company not suspended); 404 otherwise, as if it weren't there. Every user route
    about one interview starts here, so none can miss the check."""
    async with Session() as session:
        interview = await interviews.get(session, interview_id)

    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    company, member = await (require_editor if editor else require_company)(
        user, interview.company_id
    )

    return interview, company, member


async def candidate_for(
    user: CurrentUser, interview_id: UUID, invite_id: UUID, editor: bool = False
) -> tuple[Interview, CandidateInvite, Company, Member]:
    """The interview's candidate, as interview_for checks the interview; 404 when either isn't
    there or the candidate belongs to another interview."""
    async with Session() as session:
        interview = await interviews.get(session, interview_id)
        invite = await candidates.get(session, interview_id, invite_id) if interview else None

    if interview is None or invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    company, member = await (require_editor if editor else require_company)(
        user, interview.company_id
    )

    return interview, invite, company, member


async def ready_for_invites(interview: Interview, user_id: str) -> Interview:
    """The interview with its questions, for inviting: refused during the emergency pause (no
    invite, new or sent again, goes out: its candidate couldn't start) and while it has no
    questions yet (409). `user_id` is the member inviting."""
    await refuse_if_paused(get_redis(), "candidate_invite", interview.company_id, user_id)
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    return interview
