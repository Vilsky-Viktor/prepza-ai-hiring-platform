from uuid import UUID

from fastapi import APIRouter, Request
from prepza_common.auth.auth import CurrentUser, OptionalUser

from companies.schemas.invites import InviteStartOut, LinkIn, LinkOut, LinkView, StartIn
from companies.services import interview_changes, invite_pages, link_start
from companies.services.interview_access import interview_for

# One link for many candidates: a company puts it in a job ad, and each person who opens it
# takes the test as an invited candidate would.
router = APIRouter(tags=["links"])


@router.put("/interviews/{interview_id}/link")
async def set_link(interview_id: UUID, body: LinkIn, user: CurrentUser) -> LinkOut:
    """Owners and admins turn the link on (a new code) or off (it stops working at once). On
    only once it has its questions, as for an invite: visitors could otherwise hold credits for
    an interview they can't start."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)

    return LinkOut(link_token=await interview_changes.set_link(interview, body.on, user.uid))


@router.get("/links/{token}")
async def get_link(token: str, user: OptionalUser) -> LinkView:
    """Shown to anyone with the link, signed in or not, before they start. Signed in with a
    verified email, it also says how far they got, so a finished test is never offered again;
    an unverified one could claim anyone's address, so it learns nothing about that person."""
    return await invite_pages.link_view(token, user)


@router.post("/links/{token}/start")
async def start_link(
    token: str, user: CurrentUser, request: Request, body: StartIn | None = None
) -> InviteStartOut:
    """The signed-in person becomes a candidate (their verified email, one attempt each) and
    starts, with credits set aside as for an email invite. A first start takes their pledge to
    answer on their own."""
    return await link_start.start_link(token, user, request, body is not None and body.pledged)
