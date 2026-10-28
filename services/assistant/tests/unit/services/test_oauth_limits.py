import asyncio

import pytest
from fastapi import HTTPException
from mcp.server.auth.provider import AuthorizeError

from assistant.constants.limits import MAX_STATE_LENGTH
from assistant.repositories import oauth
from assistant.services import oauth_limits
from assistant.services.oauth_provider import Provider
from tests.unit.services.test_oauth_provider import CLIENT, params


@pytest.fixture
def counted(monkeypatch):
    """The limits counted, without Redis; nothing is over them."""
    keys = []

    async def hit(redis, key, name):
        keys.append((key, name))

    monkeypatch.setattr(oauth_limits, "hit_or_skip", hit)

    return keys


def test_a_registration_too_large_to_keep_is_refused(client, counted, monkeypatch):
    saved = []

    async def save_client(client_id, info):
        saved.append(info)

    monkeypatch.setattr(oauth, "save_client", save_client)
    body = {"client_name": "x" * 5_000, "redirect_uris": ["http://localhost/cb"]}

    response = client.post("/register", json=body)

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_client_metadata"
    assert saved == []


def test_requests_to_connect_are_counted_per_address(client, counted, monkeypatch):
    async def unknown(client_id):
        return None

    monkeypatch.setattr(oauth, "get_client", unknown)
    query = {
        "client_id": "unknown",
        "response_type": "code",
        "code_challenge": "challenge",
        "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
    }
    client.get("/authorize", params=query, follow_redirects=False)

    assert counted == [("rate:assistant:mcp:authorize:testclient", "AUTHORIZATIONS_PER_IP_HOUR")]


def test_too_many_requests_to_connect_from_one_address_are_refused(client, monkeypatch):
    async def over(redis, key, name):
        raise HTTPException(429, "Too many requests. Try again later.", {"Retry-After": "120"})

    monkeypatch.setattr(oauth_limits, "hit_or_skip", over)

    response = client.get("/authorize", params={"client_id": "c1"}, follow_redirects=False)

    assert response.status_code == 429
    assert response.json()["error"] == "invalid_request"
    # When the limit's window frees up.
    assert response.headers["Retry-After"] == "120"


def test_a_state_too_long_to_keep_is_refused():
    request = params().model_copy(update={"state": "s" * (MAX_STATE_LENGTH + 1)})

    with pytest.raises(AuthorizeError):
        asyncio.run(Provider().authorize(CLIENT, request))


@pytest.mark.parametrize("scheme", ["javascript", "data", "vbscript", "file"])
def test_a_return_address_that_runs_in_the_browser_is_refused(client, counted, scheme):
    body = {"redirect_uris": [f"{scheme}://claude.ai/cb"], "token_endpoint_auth_method": "none"}

    response = client.post("/register", json=body)

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_redirect_uri"


def test_a_request_to_connect_missing_its_fields_gets_a_page(client, counted):
    """Not a server error, and no redirect anywhere."""
    response = client.get("/authorize", params={"client_id": "c1"}, follow_redirects=False)

    assert response.status_code == 400
    assert "location" not in response.headers
