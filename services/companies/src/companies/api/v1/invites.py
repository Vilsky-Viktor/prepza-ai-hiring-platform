from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.auth.auth import CurrentUser, OptionalUser
from prepza_common.http.client_ip import limit_address
from prepza_common.limits.rate_limit import hit_or_skip

from companies.integrations.firebase_tokens import guest_token
from companies.integrations.redis import get_redis
from companies.schemas.invites import GuestTokenOut, InviteStartOut, InviteView, StartIn
from companies.services import candidate_start, invite_pages
from companies.services.access import open_invite

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("/{token}")
async def get_invite(token: str, user: OptionalUser) -> InviteView:
    """The invitation, also before signing in, so the page shows what it's for; whether it's the
    signed-in account's, and its email only to that account with the email verified."""
    return await invite_pages.invite_view(token, user)


@router.post("/{token}/guest")
async def sign_in_guest(token: str, request: Request) -> GuestTokenOut:
    """A sign-in for the candidate a company's own platform sent: the link is all they need."""
    invite, _ = await open_invite(token)

    if not invite.guest:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    # Each sign-in has Google sign a token: counted per address once the link proved real.
    key = f"rate:guest-sign-ins:{limit_address(request)}"
    await hit_or_skip(get_redis(), key, "GUEST_SIGN_INS_PER_IP_HOUR")

    return GuestTokenOut(token=await guest_token(invite.id))


@router.post("/{token}/start")
async def start_invite(
    token: str, user: CurrentUser, body: StartIn | None = None
) -> InviteStartOut:
    """Only the invited, verified email can start, so a forwarded link is useless to anyone else;
    a guest invite, only its guest (its link signs them in). A first start takes the candidate's
    pledge to answer on their own."""
    return await candidate_start.start_invite(token, user, body is not None and body.pledged)
