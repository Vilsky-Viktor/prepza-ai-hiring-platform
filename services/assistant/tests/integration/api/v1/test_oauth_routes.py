"""The OAuth routes against the real database and Redis: an app revoking a token, the user's
hourly limit on allowing apps, and the hourly limit per address on viewing and refusing
requests."""

import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.tokens import hashed
from prepza_common.auth.user import User
from prepza_common.config.constants import HOUR_SECONDS, RATE_LIMITED
from prepza_common.limits.limit_list import LIMITS

from assistant.constants.mcp import CONNECT_COOKIE
from assistant.integrations.redis import get_redis
from assistant.main import app
from assistant.repositories import oauth, oauth_requests
from assistant.services.oauth_provider import Provider
from tests.integration.api.v1.test_mcp import site_client
from tests.integration.repositories.test_oauth import connect
from tests.integration.transactions import transaction
from tests.unit.api.v1.test_connect import REQUEST


async def register(client_id: str) -> None:
    """An app registered without a secret, as Claude and ChatGPT register."""
    info = {
        "client_id": client_id,
        "client_name": "App",
        "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        "token_endpoint_auth_method": "none",
    }
    await transaction(oauth.save_client, client_id, info)


async def revoke(client_id: str, token: str) -> int:
    async with site_client() as site:
        response = await site.post("/revoke", data={"token": token, "client_id": client_id})

    return response.status_code


@pytest.mark.parametrize("kind", ["access_token", "refresh_token"])
def test_an_app_revoking_its_own_token_removes_the_connection(run, kind):
    user = f"revoke-{uuid.uuid4().hex[:8]}"
    client_id = uuid.uuid4().hex

    async def scenario():
        await register(client_id)
        # Another connection to the same app, which stays.
        await connect(user, client_id)
        grant, tokens = await connect(user, client_id)
        answered = await revoke(client_id, tokens[kind])

        return answered, [found.id for found in await transaction(oauth.of_user, user)], grant.id

    answered, left, revoked_id = run(scenario())

    assert answered == 200
    assert revoked_id not in left and len(left) == 1


@pytest.mark.parametrize("kind", ["access_token", "refresh_token"])
def test_an_app_cant_revoke_a_token_given_to_another_app(run, kind):
    user = f"revoke-{uuid.uuid4().hex[:8]}"
    owner, other = uuid.uuid4().hex, uuid.uuid4().hex

    async def scenario():
        await register(owner)
        await register(other)
        grant, tokens = await connect(user, owner)
        answered = await revoke(other, tokens[kind])
        works = await Provider().load_access_token(tokens["access_token"])

        return (
            answered,
            [found.id for found in await transaction(oauth.of_user, user)],
            grant.id,
            works,
        )

    answered, left, grant_id, works = run(scenario())

    # Answered as an unknown token is, so the other app learns nothing.
    assert answered == 200
    assert left == [grant_id]
    assert works is not None


@pytest.fixture
def ann():
    """A signed-in user of their own; nothing of theirs is left in Redis after the test."""
    user = User(uid=f"approve-{uuid.uuid4().hex[:8]}", email="a@example.com", email_verified=True)
    app.dependency_overrides[current_user] = lambda: user

    yield user

    app.dependency_overrides.clear()


def test_allowing_apps_over_the_hourly_limit_is_refused_and_the_request_stays(run, ann):
    key = f"rate:assistant:mcp:approve:{ann.uid}"
    first, second = f"r-{uuid.uuid4().hex}", f"r-{uuid.uuid4().hex}"

    async def approve(request_id: str):
        await oauth_requests.save_request(request_id, REQUEST)
        headers = {"Cookie": f"{CONNECT_COOKIE}={request_id}"}

        async with site_client() as site:
            return await site.post(f"/connect/{request_id}/approve", headers=headers)

    async def scenario():
        # Allowed just under the limit already this hour.
        await get_redis().set(key, LIMITS["APPROVALS_PER_USER_HOUR"].default - 1, ex=HOUR_SECONDS)
        last = await approve(first)
        over = await approve(second)
        waiting = await oauth_requests.take_request(second)
        code = parse_qs(urlparse(last.json()["redirect_url"]).query)["code"][0]
        await oauth_requests.take_code(hashed(code))
        await get_redis().delete(key)

        return last, over, waiting

    last, over, waiting = run(scenario())

    assert last.status_code == 200
    assert over.status_code == 429 and over.json()["detail"] == RATE_LIMITED
    # Refused before the request was answered: it's still there for later.
    assert waiting == REQUEST


@pytest.mark.parametrize("step", ["consent", "deny"])
def test_viewing_or_refusing_requests_over_the_hourly_limit_is_refused(run, ann, step):
    """Over the limit per address, the consent page's request is refused before it's read or
    answered: it's still there for later."""
    address = f"203.0.113.{uuid.uuid4().int % 250 + 1}"
    key = f"rate:assistant:mcp:{step}:{address}"
    request_id = f"r-{uuid.uuid4().hex}"
    # The load balancer's X-Forwarded-For: the visitor, then the balancer.
    headers = {
        "Cookie": f"{CONNECT_COOKIE}={request_id}",
        "X-Forwarded-For": f"{address}, 10.0.0.1",
    }

    async def ask(site):
        if step == "consent":
            return await site.get(f"/connect/{request_id}", headers=headers)

        return await site.post(f"/connect/{request_id}/deny", headers=headers)

    async def scenario():
        await get_redis().delete(key)
        await oauth_requests.save_request(request_id, REQUEST)
        await get_redis().set(key, LIMITS["AUTHORIZATIONS_PER_IP_HOUR"].default, ex=HOUR_SECONDS)

        async with site_client() as site:
            over = await ask(site)

        waiting = await oauth_requests.take_request(request_id)
        await get_redis().delete(key)

        return over, waiting

    over, waiting = run(scenario())

    assert over.status_code == 429 and over.json()["detail"] == RATE_LIMITED
    assert int(over.headers["Retry-After"]) > 0
    assert waiting == REQUEST
