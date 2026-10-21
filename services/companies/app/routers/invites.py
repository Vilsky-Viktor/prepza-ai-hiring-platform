from fastapi import APIRouter, HTTPException, status
from prepza_common.auth import CurrentUser, OptionalUser
from prepza_common.pause import refuse_if_paused

from app.constants.invites import EMAIL_NOT_VERIFIED, NOT_THE_GUEST, InviteStatus
from app.helpers.brand import color_sets, style_of
from app.helpers.candidates import candidate_seconds
from app.helpers.interviews import attach_set, interview_minutes, interview_title
from app.helpers.logos import logo_path
from app.integrations.firebase_tokens import guest_token, guest_uid
from app.integrations.redis import get_redis
from app.schemas.invites import GuestTokenOut, InviteStartOut, InviteView, StartIn
from app.schemas.logos import BrandColorSets, BrandStyle
from app.services import set_cache
from app.services.access import open_invite, refuse_if_suspended, refuse_without_pledge
from app.services.candidate_start import start_sessions
from app.storage import companies

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("/{token}")
async def get_invite(token: str, user: OptionalUser) -> InviteView:
    """The invitation, also before signing in, so the page shows what it's for; the candidate's
    email only once someone is signed in."""
    # An expired invite's link stops working until the company sends it again.
    invite, interview = await open_invite(token)
    interview = await attach_set(interview)
    title = await interview_title(interview)

    company = await companies.get(interview.company_id)
    refuse_if_suspended(company, invite.status)
    seconds = candidate_seconds(interview.question_seconds, invite.extra_time)
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None

    return InviteView(
        interview_id=interview.id,
        title=title,
        company=company.name if company else "",
        logo_url=logo_path(company),
        verified_domain=company.verified_domain if company else None,
        email=invite.email if user else None,
        status=invite.status,
        question_seconds=seconds,
        total_minutes=interview_minutes(found, interview.topic_limits, seconds),
        guest=invite.guest,
        brand_colors=BrandColorSets(**color_sets(company.brand_colors if company else None)),
        theme=invite.theme,
        brand_style=BrandStyle(**style_of(company)),
        embed_domain=company.verified_domain if company and invite.guest else None,
    )


@router.post("/{token}/guest")
async def sign_in_guest(token: str) -> GuestTokenOut:
    """A sign-in for the candidate a company's own platform sent: the link is all they need."""
    invite, _ = await open_invite(token)

    if not invite.guest:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    return GuestTokenOut(token=await guest_token(invite.id))


@router.post("/{token}/start")
async def start_invite(
    token: str, user: CurrentUser, body: StartIn | None = None
) -> InviteStartOut:
    """Only the invited, verified email can start, so a forwarded link is useless to anyone else;
    a guest invite, only its guest (its link signs them in). A first start takes the candidate's
    pledge to answer on their own."""
    invite, interview = await open_invite(token)

    if invite.guest:
        if user.uid != guest_uid(invite.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_THE_GUEST)
    elif not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)
    elif user.email.lower() != invite.email:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This invite was sent to a different email address"
        )

    if invite.status == InviteStatus.FINISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "This interview is already finished")

    refuse_if_suspended(await companies.get(interview.company_id), invite.status)
    refuse_without_pledge(body is not None and body.pledged, invite.status)

    # Paused, nobody starts; a candidate already in the interview may finish it.
    if invite.status != InviteStatus.IN_PROCESS:
        await refuse_if_paused(get_redis(), "interview_start", interview.company_id, user.uid)

    return await start_sessions(invite, interview, user)
