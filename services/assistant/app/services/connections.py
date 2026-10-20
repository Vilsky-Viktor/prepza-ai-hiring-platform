import time
from uuid import UUID

from fastapi import HTTPException, status
from mcp.server.auth.provider import construct_redirect_uri
from prepza_common.analytics import track
from prepza_common.rate_limit import hit
from prepza_common.tokens import new_token
from prepza_common.user import User

from app.constants.mcp import CODE_BYTES, CODE_SECONDS, NOT_FOUND, OTHER_BROWSER
from app.helpers.oauth import auth_settings
from app.integrations.redis import get_redis
from app.models.oauth import McpGrant
from app.storage import oauth, oauth_requests


async def describe(request_id: str) -> dict:
    """What the consent page shows of an app's request: its name, the site it returns to and
    whether prepza knows it; a 404 once it's answered or expired."""
    found = await oauth_requests.peek_request(request_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    return {key: found[key] for key in ("client_name", "redirect_host", "known_client")}


async def approve(request_id: str, user: User, marked: str | None) -> str:
    """The user allows the app: a single-use code bound to them, which the app exchanges for
    its tokens. Where the browser goes next: back to the app, with the code. Only from the
    browser that asked (`marked`, its connect cookie): a link someone else started is refused,
    and the request stays for its own browser."""
    if marked != request_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, OTHER_BROWSER)

    key = f"rate:assistant:mcp:approve:{user.uid}"
    await hit(get_redis(), key, "APPROVALS_PER_USER_HOUR", user_id=user.uid)
    found = await taken(request_id)
    code, code_hash = new_token("", CODE_BYTES)
    kept = {**found, "user_id": user.uid, "expires_at": time.time() + CODE_SECONDS}
    await oauth_requests.save_code(code_hash, kept)

    return construct_redirect_uri(
        found["redirect_uri"], code=code, state=found["state"], iss=issuer()
    )


async def deny(request_id: str) -> str:
    """The user refuses: back to the app, which learns it was denied."""
    found = await taken(request_id)

    return construct_redirect_uri(
        found["redirect_uri"], error="access_denied", state=found["state"], iss=issuer()
    )


def issuer() -> str:
    """Who answers, in every answer to an app (RFC 9207): an app talking to several
    authorization servers can tell this answer is prepza's (mix-up attacks)."""

    return str(auth_settings().issuer_url)


async def taken(request_id: str) -> dict:
    """The request, taken for this answer alone; a 404 once it's answered or expired."""
    found = await oauth_requests.take_request(request_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    return found


async def of_user(user_id: str) -> list[McpGrant]:
    return await oauth.of_user(user_id)


async def disconnect(grant_id: UUID, user_id: str) -> None:
    """The user disconnects one of their apps; its tokens stop working at once. A 404 for one
    that isn't theirs."""
    removed = await oauth.remove(grant_id, user_id)

    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    await track("mcp_disconnected", user_id=user_id, by="user")
