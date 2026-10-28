import time
from uuid import UUID

from fastapi import HTTPException, status
from mcp.server.auth.provider import construct_redirect_uri
from prepza_common.auth.tokens import new_token
from prepza_common.auth.user import User
from prepza_common.events.analytics import track
from prepza_common.limits.rate_limit import hit_or_skip

from assistant.constants.mcp import CODE_BYTES, CODE_SECONDS, MCP_SCOPE, NOT_FOUND, OTHER_BROWSER
from assistant.core.db import Session
from assistant.helpers.oauth import auth_settings, granted_scope
from assistant.integrations.redis import get_redis
from assistant.models.oauth import McpGrant
from assistant.repositories import oauth, oauth_requests


async def describe(request_id: str, address: str, user_id: str) -> dict:
    """What the consent page shows of an app's request: its name, the site it returns to and
    whether prepza knows it; a 404 once it's answered or expired. Counted per `address`
    against the connection requests' limit, so request ids can't be tried in bulk."""
    await count_consent("consent", address, user_id)
    found = await oauth_requests.peek_request(request_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    described = {key: found[key] for key in ("client_name", "redirect_host", "known_client")}

    return {**described, "read_only": MCP_SCOPE not in found["scopes"]}


async def approve(request_id: str, user: User, marked: str | None, read_only: bool = False) -> str:
    """The user allows the app: a single-use code bound to them and to what they allowed (only
    reading when the app asked for no more, or the user chose it), which the app exchanges for
    its tokens. Where the browser goes next: back to the app, with the code. Only from the
    browser that asked (`marked`, its connect cookie): a link someone else started is refused,
    and the request stays for its own browser."""
    if marked != request_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, OTHER_BROWSER)

    key = f"rate:assistant:mcp:approve:{user.uid}"
    # Against floods, not spend: with Redis down, not counted rather than refused.
    await hit_or_skip(get_redis(), key, "APPROVALS_PER_USER_HOUR", user_id=user.uid)
    found = await taken(request_id)
    code, code_hash = new_token("", CODE_BYTES)
    scope = granted_scope(found["scopes"], read_only)
    kept = {
        **found,
        "scopes": [scope],
        "user_id": user.uid,
        "expires_at": time.time() + CODE_SECONDS,
    }
    await oauth_requests.save_code(code_hash, kept)

    return construct_redirect_uri(
        found["redirect_uri"], code=code, state=found["state"], iss=issuer()
    )


async def deny(request_id: str, marked: str | None, address: str, user_id: str) -> str:
    """The user refuses: back to the app, which learns it was denied. Only from the browser that
    asked (`marked`), so someone else holding the request's id can't end it. Counted per
    `address`, as viewing the request is."""
    if marked != request_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, OTHER_BROWSER)

    await count_consent("deny", address, user_id)
    found = await taken(request_id)

    return construct_redirect_uri(
        found["redirect_uri"], error="access_denied", state=found["state"], iss=issuer()
    )


async def count_consent(step: str, address: str, user_id: str) -> None:
    """Counts one step of the consent page (`step`) from `address` against the connection
    requests' limit per address, as /authorize is; over it, refused (429). Against floods: with
    Redis down, not counted rather than refused."""
    key = f"rate:assistant:mcp:{step}:{address}"
    await hit_or_skip(get_redis(), key, "AUTHORIZATIONS_PER_IP_HOUR", user_id=user_id)


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
    async with Session() as session:
        return await oauth.of_user(session, user_id)


async def disconnect(grant_id: UUID, user_id: str) -> None:
    """The user disconnects one of their apps; its tokens stop working at once. A 404 for one
    that isn't theirs."""
    async with Session.begin() as session:
        removed = await oauth.remove(session, grant_id, user_id)

    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    await track("mcp_disconnected", user_id=user_id, by="user")
