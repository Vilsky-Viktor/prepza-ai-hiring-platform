from uuid import UUID

from fastapi import APIRouter, Request, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.http.client_ip import limit_address

from assistant.constants.mcp import CONNECT_COOKIE
from assistant.schemas.connect import ApproveIn, ConnectionOut, ConnectRequestOut, RedirectOut
from assistant.services import connections

router = APIRouter(tags=["connect"])


@router.get("/connect/{request_id}")
async def connect_request(
    request_id: str, user: CurrentUser, request: Request
) -> ConnectRequestOut:
    """An AI app's request to connect to the signed-in user's account, for the consent page; a
    404 once it's answered or expired. Counted per address, so request ids can't be tried in
    bulk (429)."""
    described = await connections.describe(request_id, limit_address(request), user.uid)

    return ConnectRequestOut(**described)


@router.post("/connect/{request_id}/approve")
async def approve(
    request_id: str, user: CurrentUser, request: Request, body: ApproveIn | None = None
) -> RedirectOut:
    """The user allows the app to use prepza as them (only to read, with `read_only`): back to
    the app with a single-use code. Only from the browser that asked to connect (its cookie); a
    403 from any other."""
    marked = request.cookies.get(CONNECT_COOKIE)
    read_only = body.read_only if body else False
    url = await connections.approve(request_id, user, marked, read_only)

    return RedirectOut(redirect_url=url)


@router.post("/connect/{request_id}/deny")
async def deny(request_id: str, user: CurrentUser, request: Request) -> RedirectOut:
    """The user refuses: back to the app, which learns it was denied. Only from the browser that
    asked to connect, as approving; a 403 from any other. Counted per address (429)."""
    marked = request.cookies.get(CONNECT_COOKIE)
    url = await connections.deny(request_id, marked, limit_address(request), user.uid)

    return RedirectOut(redirect_url=url)


@router.get("/connections")
async def list_connections(user: CurrentUser) -> list[ConnectionOut]:
    """The AI apps the signed-in user connected, the latest first."""
    return [ConnectionOut.model_validate(grant) for grant in await connections.of_user(user.uid)]


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(connection_id: UUID, user: CurrentUser) -> None:
    """Disconnects one of the user's apps: its access stops at once."""
    await connections.disconnect(connection_id, user.uid)
