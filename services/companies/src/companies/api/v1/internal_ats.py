from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from companies.api.dependencies import ServiceCaller
from companies.constants.audit import VIA_API, VIA_ATS
from companies.core.db import Session
from companies.repositories import companies, interviews
from companies.schemas.internal_ats import AccessOut, AtsInviteIn, AtsInviteOut, InterviewBriefOut
from companies.services import ats_invites
from companies.services.access import (
    ai_apps_refusal,
    can_edit,
    key_refusal,
    member_of,
    suspension_refusal,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/companies/{company_id}/access")
async def access(company_id: UUID, user_id: str, caller: ServiceCaller) -> AccessOut:
    """What the user may do in the company: ats, notifications and the api guard their pages
    with it (prepza_common.auth.company_access), refusing what companies' own routes refuse: the
    caller passes on the assistant's X-Assistant header. A company that doesn't exist is 404."""
    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    member = member_of(company, user_id)

    return AccessOut(
        member=member is not None,
        editor=member is not None and can_edit(member),
        refused=key_refusal(company_id) or ai_apps_refusal(company),
        read_only=suspension_refusal(company),
    )


@router.get("/interviews")
async def interviews_by_ids(
    ids: Annotated[list[UUID], Query()], caller: ServiceCaller
) -> list[InterviewBriefOut]:
    """The interviews of those ids that still exist, for ats's linked jobs."""
    async with Session() as session:
        found = await interviews.by_ids(session, ids)

    return [
        InterviewBriefOut(
            id=item.id, company_id=item.company_id, title=item.title, ready=item.set_id is not None
        )
        for item in found
    ]


@router.post("/interviews/{interview_id}/invites", status_code=status.HTTP_201_CREATED)
async def invite(
    interview_id: UUID, body: AtsInviteIn, caller: ServiceCaller, response: Response
) -> AtsInviteOut:
    """A candidate an ATS sent is invited, as the member who connected it. Refused with 503
    during the emergency pause, 402 without credits and 429 over the email limits; 404 when the
    interview is gone, 409 while it has no questions yet, and 403 when that member is no longer
    an owner or admin (a removed member's connection invites no one). A candidate who already
    finished is returned as they are (200), and so is one still invited when `resend` is
    false."""
    invite_id, created = await ats_invites.invite(
        interview_id, body, VIA_API if caller == VIA_API else VIA_ATS
    )

    # Nothing new was made.
    if not created:
        response.status_code = status.HTTP_200_OK

        return AtsInviteOut(invite_id=invite_id, created=False)

    return AtsInviteOut(invite_id=invite_id)
