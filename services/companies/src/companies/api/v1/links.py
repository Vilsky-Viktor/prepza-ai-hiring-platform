import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.auth.auth import CurrentUser, OptionalUser
from prepza_common.events.audit_actions import AuditAction

from companies.constants.invites import (
    EMAIL_NOT_VERIFIED,
    INTERVIEW_NOT_READY,
    LINK_TOKEN_BYTES,
    InviteStatus,
)
from companies.helpers.brand import color_sets, style_of
from companies.helpers.candidates import new_hold_key
from companies.helpers.interviews import attach_set, interview_minutes, interview_title
from companies.helpers.logos import logo_path
from companies.repositories import audit, companies, interviews, invites
from companies.schemas.invites import InviteStartOut, LinkIn, LinkOut, LinkView, StartIn
from companies.schemas.logos import BrandColorSets, BrandStyle
from companies.services import link_start, set_cache
from companies.services.access import refuse_if_suspended, refuse_without_pledge
from companies.services.interview_access import interview_for, ready_for_invites

# One link for many candidates: a company puts it in a job ad, and each person who opens it
# takes the test as an invited candidate would.
router = APIRouter(tags=["links"])


async def linked_interview(token: str):
    interview = await interviews.get_by_link(token)

    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")

    return interview


@router.put("/interviews/{interview_id}/link")
async def set_link(interview_id: UUID, body: LinkIn, user: CurrentUser) -> LinkOut:
    """Owners and admins turn the link on (a new code) or off (it stops working at once). On
    only once it has its questions, as for an invite: visitors could otherwise hold credits for
    an interview they can't start."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)

    if body.on:
        await ready_for_invites(interview, user.uid)

    token = (interview.link_token or secrets.token_urlsafe(LINK_TOKEN_BYTES)) if body.on else None
    await interviews.set_link(interview.id, token)
    action = AuditAction.LINK_TURNED_ON if body.on else AuditAction.LINK_TURNED_OFF
    await audit.record_interview(interview, user.uid, action)

    return LinkOut(link_token=token)


@router.get("/links/{token}")
async def get_link(token: str, user: OptionalUser) -> LinkView:
    """Shown to anyone with the link, signed in or not, before they start. Signed in with a
    verified email, it also says how far they got, so a finished test is never offered again;
    an unverified one could claim anyone's address, so it learns nothing about that person."""
    interview = await attach_set(await linked_interview(token))
    company = await companies.get(interview.company_id)
    verified = user is not None and user.email_verified
    status_now = await invites.status_of(interview.id, user.email) if verified else None
    refuse_if_suspended(company, status_now)
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None

    return LinkView(
        title=await interview_title(interview),
        company=company.name if company else "",
        logo_url=logo_path(company),
        verified_domain=company.verified_domain if company else None,
        brand_colors=BrandColorSets(**color_sets(company.brand_colors if company else None)),
        brand_style=BrandStyle(**style_of(company)),
        question_seconds=interview.question_seconds,
        total_minutes=interview_minutes(found, interview.topic_limits, interview.question_seconds),
        status=status_now,
    )


@router.post("/links/{token}/start")
async def start_link(
    token: str, user: CurrentUser, request: Request, body: StartIn | None = None
) -> InviteStartOut:
    """The signed-in person becomes a candidate (their verified email, one attempt each) and
    starts, with credits set aside as for an email invite. A first start takes their pledge to
    answer on their own."""
    interview = await linked_interview(token)

    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)

    # A link turned on before its questions were made holds nothing until they are.
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    current, stored = await invites.held(interview.id, user.email)
    refuse_without_pledge(body is not None and body.pledged, current)
    key = stored if current else new_hold_key(interview.id)
    await link_start.admit(interview, user, current, request)
    # Credits set aside just now: a new candidate's, or an expired invite's (expiry gave them
    # back, and won't again). Anything failing before the candidate has started gives them back.
    fresh = current is None or current == InviteStatus.EXPIRED
    await link_start.hold_credits(interview, key, current, fresh)
    invite = await link_start.save_invite(interview, user, key, current, fresh)

    return await link_start.start(invite, interview, user, key, current)
