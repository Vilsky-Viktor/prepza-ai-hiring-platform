import asyncio
import time
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from mcp.server.auth.provider import AuthorizationParams, AuthorizeError, TokenError
from mcp.shared.auth import OAuthClientInformationFull
from prepza_common.auth.tokens import hashed

from assistant.repositories import oauth, oauth_requests
from assistant.services import oauth_limits, oauth_provider
from assistant.services.oauth_provider import Provider

CLIENT = OAuthClientInformationFull(
    client_id="c1",
    client_name="Claude",
    redirect_uris=["https://claude.ai/api/mcp/auth_callback"],
    token_endpoint_auth_method="none",
)
RESOURCE = "http://localhost:8090/mcp"


@pytest.fixture
def kept(monkeypatch):
    """Requests and codes (Redis) and connections (Postgres), in memory."""
    store = SimpleNamespace(requests={}, codes={}, grants={}, tracked=[])

    async def save_request(request_id, request):
        store.requests[request_id] = request

    async def save_code(code_hash, code):
        store.codes[code_hash] = code

    async def peek_code(code_hash):
        return store.codes.get(code_hash)

    async def take_code(code_hash):
        return store.codes.pop(code_hash, None)

    async def add_grant(grant):
        grant.id = uuid.uuid4()
        store.grants[grant.id] = grant

        return grant

    def finder(field):
        async def find(value):
            return next((g for g in store.grants.values() if getattr(g, field) == value), None)

        return find

    async def rotate(grant_id, refresh_hash, values):
        grant = store.grants.get(grant_id)

        if grant is None or grant.refresh_hash != refresh_hash:
            return False

        for name, value in values.items():
            setattr(grant, name, value)

        grant.previous_refresh_hash = refresh_hash
        grant.refreshed_at = datetime.now(UTC)

        return True

    async def remove(grant_id, user_id=None):
        return store.grants.pop(grant_id, None)

    async def track(event, **props):
        store.tracked.append((event, props))

    async def nothing(*args, **kwargs):
        pass

    for name, fake in {
        "save_request": save_request,
        "save_code": save_code,
        "peek_code": peek_code,
        "take_code": take_code,
    }.items():
        monkeypatch.setattr(oauth_requests, name, fake)

    monkeypatch.setattr(oauth, "add_grant", add_grant)
    monkeypatch.setattr(oauth, "by_access", finder("access_hash"))
    monkeypatch.setattr(oauth, "by_refresh", finder("refresh_hash"))
    monkeypatch.setattr(oauth, "by_previous_refresh", finder("previous_refresh_hash"))
    monkeypatch.setattr(oauth, "rotate", rotate)
    monkeypatch.setattr(oauth, "remove", remove)
    monkeypatch.setattr(oauth_provider, "track", track)
    monkeypatch.setattr(oauth_limits, "hit_or_skip", nothing)

    return store


def params(resource: str | None = RESOURCE) -> AuthorizationParams:
    return AuthorizationParams(
        state="s1",
        scopes=["prepza"],
        code_challenge="challenge",
        redirect_uri="https://claude.ai/api/mcp/auth_callback",
        redirect_uri_provided_explicitly=True,
        resource=resource,
    )


def allowed(store, user_id: str = "ann") -> str:
    """A code the user's allowing gave the app (as the consent page's approve does)."""
    [request] = store.requests.values()
    store.codes[hashed("code-1")] = {**request, "user_id": user_id, "expires_at": time.time() + 60}

    return "code-1"


def test_authorizing_keeps_the_request_and_sends_the_user_to_the_consent_page(kept):
    url = asyncio.run(Provider().authorize(CLIENT, params()))

    [(request_id, request)] = kept.requests.items()
    assert url == f"http://localhost:8090/connect?request={request_id}"
    assert (request["client_name"], request["redirect_host"], request["known_client"]) == (
        "Claude",
        "claude.ai",
        True,
    )
    # No resource named: it's for the MCP endpoint, the only one.
    asyncio.run(Provider().authorize(CLIENT, params(None)))


def test_access_for_another_resource_is_refused(kept):
    with pytest.raises(AuthorizeError) as refused:
        asyncio.run(Provider().authorize(CLIENT, params("https://evil.example/mcp")))

    assert refused.value.error == "invalid_target"


def test_a_code_is_exchanged_once_for_the_users_tokens(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    tokens = asyncio.run(provider.exchange_authorization_code(CLIENT, code))

    [grant] = kept.grants.values()
    assert (grant.user_id, grant.client_name, code.resource) == ("ann", "Claude", RESOURCE)
    assert grant.access_hash == hashed(tokens.access_token)
    assert tokens.access_token.startswith("pzm_") and tokens.expires_in == 3600
    assert kept.tracked == [("mcp_connected", {"user_id": "ann", "client": "claude"})]

    with pytest.raises(TokenError):
        asyncio.run(provider.exchange_authorization_code(CLIENT, code))


def test_a_read_only_connection_stays_read_only_after_a_refresh(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code_id = allowed(kept)
    kept.codes[hashed(code_id)]["scopes"] = ["prepza:read"]
    code = asyncio.run(provider.load_authorization_code(CLIENT, code_id))
    first = asyncio.run(provider.exchange_authorization_code(CLIENT, code))
    refresh = asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token))
    second = asyncio.run(provider.exchange_refresh_token(CLIENT, refresh, []))

    [grant] = kept.grants.values()
    assert grant.scope == first.scope == second.scope == "prepza:read"
    assert asyncio.run(provider.load_access_token(second.access_token)).scopes == ["prepza:read"]


def test_a_full_connection_can_also_read(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    tokens = asyncio.run(provider.exchange_authorization_code(CLIENT, code))

    assert tokens.scope == "prepza"
    access = asyncio.run(provider.load_access_token(tokens.access_token))
    assert set(access.scopes) == {"prepza", "prepza:read"}


def test_another_apps_code_isnt_found(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    other = CLIENT.model_copy(update={"client_id": "c2"})

    assert asyncio.run(provider.load_authorization_code(other, allowed(kept))) is None


def test_a_refresh_replaces_both_tokens_and_the_old_ones_stop_working(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    first = asyncio.run(provider.exchange_authorization_code(CLIENT, code))
    refresh = asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token))
    second = asyncio.run(provider.exchange_refresh_token(CLIENT, refresh, ["prepza"]))

    assert asyncio.run(provider.load_access_token(first.access_token)) is None
    assert asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token)) is None
    assert asyncio.run(provider.load_access_token(second.access_token)).subject == "ann"

    # The same refresh token again (a race lost): refused.
    with pytest.raises(TokenError):
        asyncio.run(provider.exchange_refresh_token(CLIENT, refresh, ["prepza"]))


def test_a_replaced_refresh_token_used_again_later_revokes_the_connection(kept):
    """Right after its refresh it's an app refreshing twice at once, only refused; later, likely
    a stolen copy: the connection goes, and the app asks the user again."""
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    first = asyncio.run(provider.exchange_authorization_code(CLIENT, code))
    refresh = asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token))
    second = asyncio.run(provider.exchange_refresh_token(CLIENT, refresh, ["prepza"]))
    [grant] = kept.grants.values()

    assert asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token)) is None
    assert grant.id in kept.grants

    grant.refreshed_at = datetime.now(UTC) - timedelta(minutes=2)

    assert asyncio.run(provider.load_refresh_token(CLIENT, first.refresh_token)) is None
    assert kept.grants == {}
    assert asyncio.run(provider.load_access_token(second.access_token)) is None


def test_an_expired_access_token_is_refused(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    tokens = asyncio.run(provider.exchange_authorization_code(CLIENT, code))
    [grant] = kept.grants.values()
    grant.access_expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert asyncio.run(provider.load_access_token(tokens.access_token)) is None


def test_revoking_deletes_the_connection(kept):
    provider = Provider()
    asyncio.run(provider.authorize(CLIENT, params()))
    code = asyncio.run(provider.load_authorization_code(CLIENT, allowed(kept)))
    tokens = asyncio.run(provider.exchange_authorization_code(CLIENT, code))
    access = asyncio.run(provider.load_access_token(tokens.access_token))
    asyncio.run(provider.revoke_token(access))

    assert kept.grants == {}
    assert kept.tracked[-1] == ("mcp_disconnected", {"user_id": "ann", "by": "client"})
