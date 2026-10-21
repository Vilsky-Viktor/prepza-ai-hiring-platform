from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.pause import refuse_if_paused
from prepza_common.user import User

from app.constants.audit import VIA_API, VIA_ATS
from app.constants.invites import OPEN, RETURN_URL_OFF_DOMAIN, InviteStatus
from app.helpers.return_urls import on_domain
from app.integrations.redis import get_redis
from app.schemas.internal_ats import AccessOut, AtsInviteIn, AtsInviteOut, InterviewBriefOut
from app.service_auth import ServiceCaller
from app.services import candidate_invites
from app.services import outbox as outbox_service
from app.services.access import (
    ai_apps_refusal,
    can_edit,
    key_refusal,
    member_of,
    suspension_refusal,
)
from app.storage import companies, interviews, invites

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/companies/{company_id}/access")
async def access(company_id: UUID, user_id: str, caller: ServiceCaller) -> AccessOut:
    """What the user may do in the company: ats, notifications and the api guard their pages
    with it (prepza_common.company_access), refusing what companies' own routes refuse: the
    caller passes on the assistant's X-Assistant header. A company that doesn't exist is 404."""
    company = await companies.get(company_id)

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
    return [
        InterviewBriefOut(
            id=item.id, company_id=item.company_id, title=item.title, ready=item.set_id is not None
        )
        for item in await interviews.by_ids(ids)
    ]


@router.post("/interviews/{interview_id}/invites", status_code=status.HTTP_201_CREATED)
async def invite(interview_id: UUID, body: AtsInviteIn, caller: ServiceCaller) -> AtsInviteOut:
    """A candidate an ATS sent is invited, as the member who connected it. Refused with 503
    during the emergency pause, 402 without credits and 429 over the email limits; 404 when the
    interview is gone, 409 while it has no questions yet, and 403 when that member is no longer
    an owner or admin (a removed member's connection invites no one). A candidate who already
    finished is returned as they are, and so is one still invited when `resend` is false."""
    interview = await interviews.get(interview_id)

    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "The interview isn't ready yet")

    await refuse_if_paused(get_redis(), "candidate_invite", interview.company_id, body.sender_id)
    company = await companies.get(interview.company_id)
    sender = member_of(company, body.sender_id)

    if sender is None or not can_edit(sender):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only an owner or admin can invite")

    if body.return_url and not on_domain(body.return_url, company.verified_domain):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, RETURN_URL_OFF_DOMAIN)

    # A candidate who already finished keeps their results, and isn't emailed again; nor is one
    # whose invite is still open, when the caller asked for no resend (the API's retries).
    found = await invites.find(interview_id, str(body.email))
    kept = (InviteStatus.FINISHED,) if body.resend else (InviteStatus.FINISHED, *OPEN)

    if found is not None and found.status in kept:
        return AtsInviteOut(invite_id=found.id, created=False)

    user = User(uid=body.sender_id, email="", email_verified=True)
    sent = await candidate_invites.invite(
        interview,
        company,
        user,
        body.email,
        body.name,
        body.return_url,
        body.sign_in,
        body.theme,
        via=VIA_API if caller == VIA_API else VIA_ATS,
    )
    await outbox_service.flush_quietly()

    return AtsInviteOut(invite_id=sent.id)
