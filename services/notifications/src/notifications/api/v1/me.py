from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from testee_common.auth.auth import CurrentUser, FreshUser
from testee_common.http.sse import event_stream
from testee_common.i18n.i18n import request_language

from notifications.schemas.legal_notices import LegalChangeOut
from notifications.schemas.notifications import FeedOut
from notifications.services import legal_notices, notices
from notifications.services.feed import feed, open_stream

router = APIRouter(prefix="/me", tags=["notifications"])


@router.get("")
async def get_feed(user: CurrentUser, request: Request, fresh: bool = False) -> FeedOut:
    """The bell: the latest notifications, the user's own, their companies' and everyone's
    newer than their account, and how many came since they last opened it, in their language;
    `fresh` reads the companies again (right after joining)."""
    return await feed(user.uid, request_language(request), fresh)


@router.get("/legal-changes")
async def legal_changes(user: CurrentUser) -> list[LegalChangeOut]:
    """The legal documents' new versions noticed and not yet in force that concern the user,
    for the site's banner until they apply."""
    return [LegalChangeOut(**item) for item in await legal_notices.upcoming(user.uid)]


@router.post("/seen", status_code=status.HTTP_204_NO_CONTENT)
async def mark_seen(user: CurrentUser) -> None:
    """Opening the bell: everything so far counts as read."""
    await notices.mark_seen(user.uid)


@router.get("/stream")
async def stream(user: FreshUser, fresh: bool = False) -> StreamingResponse:
    """Server-sent events while a tab is open: {"new": true} as soon as a notification comes,
    so the bell reloads; heartbeat comments in between. At most STREAMS_PER_USER at once;
    the bell refreshes on its own without one."""
    return event_stream(await open_stream(user.uid, fresh))
