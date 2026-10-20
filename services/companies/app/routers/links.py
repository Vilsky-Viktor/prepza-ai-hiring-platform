import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.analytics import track
from prepza_common.audit_actions import AuditAction
from prepza_common.auth import CurrentUser, OptionalUser
from prepza_common.client_ip import client_ip
from prepza_common.human_check import require_human
from prepza_common.pause import refuse_if_paused
from prepza_common.rate_limit import hit

from app.config.settings import settings
from app.constants.invites import (
    EMAIL_NOT_VERIFIED,
    INTERVIEW_NOT_READY,
    LINK_CLOSED,
    LINK_TOKEN_BYTES,
    NOT_STARTED,
    InviteStatus,
)
from app.helpers.brand import color_sets, style_of
from app.helpers.candidates import new_hold_key
from app.helpers.interviews import attach_set, interview_minutes, interview_title
from app.helpers.logos import logo_path
from app.integrations import billing
from app.integrations.redis import get_redis
from app.schemas.invites import InviteStartOut, LinkIn, LinkOut, LinkView
from app.schemas.logos import BrandColorSets, BrandStyle
from app.services import outbox as outbox_service
from app.services import set_cache
from app.services.access import refuse_if_suspended
from app.services.candidate_start import start_sessions
from app.services.interview_access import interview_for, ready_for_invites
from app.storage import audit, companies, interviews, invites, link_invites

# One link for many candidates: a company puts it in a job ad, and each person who opens it
# takes the test as an invited candidate would.
router = APIRouter(tags=["links"])


async def linked_interview(token: str):
    interview = await interviews.get_by_link(token)

    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")

    return interview


async def joined_details(interview) -> dict:
    """What a new candidate's email with their own link says: the test and who it's for."""
    company = await companies.get(interview.company_id)

    return {
        "title": await interview_title(interview) or "an interview",
        "company": company.name if company else "",
        "language": interview.language,
        "logo_path": logo_path(company),
    }


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
async def start_link(token: str, user: CurrentUser, request: Request) -> InviteStartOut:
    """The signed-in person becomes a candidate (their verified email, one attempt each) and
    starts, with credits set aside as for an email invite."""
    interview = await linked_interview(token)

    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)

    # A link turned on before its questions were made holds nothing until they are.
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    current, stored = await invites.held(interview.id, user.email)
    key = stored if current else new_hold_key(interview.id)

    if current == InviteStatus.FINISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "This interview is already finished")

    refuse_if_suspended(await companies.get(interview.company_id), current)

    # Paused, nobody starts; a candidate already in the interview may finish it.
    if current != InviteStatus.IN_PROCESS:
        await refuse_if_paused(get_redis(), "interview_start", interview.company_id, user.uid)

    # A new candidate shows they're a person and counts toward the link's and their address's
    # hourly limits; one already invited is never held back by them.
    if current is None:
        await require_human(request, settings.turnstile_secret_key)
        redis = get_redis()
        who = {"company_id": interview.company_id, "user_id": user.uid}
        link_key = f"rate:link-starts:{interview.id}"
        await hit(redis, link_key, "LINK_STARTS_PER_HOUR", **who)
        address = client_ip(request)
        await hit(redis, f"rate:link-starts:ip:{address}", "LINK_STARTS_PER_IP_HOUR", **who)

    # Credits set aside just now: a new candidate's, or an expired invite's (expiry gave them
    # back, and won't again). Anything failing before the candidate has started gives them back.
    fresh = current is None or current == InviteStatus.EXPIRED

    if current is None or current in NOT_STARTED:
        try:
            await billing.hold_candidate(interview.company_id, key)
        except HTTPException as error:
            if error.status_code == status.HTTP_402_PAYMENT_REQUIRED:
                raise HTTPException(status.HTTP_409_CONFLICT, LINK_CLOSED) from error

            raise
        except Exception:
            # Billing's answer lost on the way: a hold made just now may exist. An invite's
            # earlier hold stays.
            if fresh:
                await billing.release_candidate(key)

            raise

    try:
        details = await joined_details(interview) if current is None else None
        invite = await link_invites.for_link(
            interview.id, user.email, hold_key=key, details=details
        )
    except Exception:
        # An invite that couldn't be saved (its interview deleted meanwhile) gives its credits
        # back.
        if fresh:
            await billing.release_candidate(key)

        raise

    # Started at the same moment by another request, whose own key and credits were kept.
    if current is None and invite.hold_key != key:
        await billing.release_candidate(key)

    if current is None:
        await outbox_service.flush_quietly()
        await track("candidate_joined_by_link", company_id=interview.company_id)

    try:
        return await start_sessions(invite, interview, user)
    except Exception:
        # An expired invite that didn't start stays expired, and expiry won't give its credits
        # back: they go back now. A new one waits, unstarted, until it expires.
        if current == InviteStatus.EXPIRED:
            await billing.release_candidate(key)

        raise
