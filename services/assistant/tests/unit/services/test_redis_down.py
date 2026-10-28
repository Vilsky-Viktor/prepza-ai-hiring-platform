"""With Redis down, the limits against abuse (apps registering, asking for tokens and calling
tools) go uncounted rather than refusing every app."""

import asyncio

import pytest
from fake_redis import DownRedis
from starlette.requests import Request

from assistant.repositories import oauth
from assistant.services import mcp_tools, oauth_limits
from tests.unit.services.test_mcp_tools import ACCESS


@pytest.fixture
def down(monkeypatch):
    redis = DownRedis()
    monkeypatch.setattr(oauth_limits, "get_redis", lambda: redis)
    monkeypatch.setattr(mcp_tools, "get_redis", lambda: redis)


def test_an_app_registers_with_redis_down(client, down, monkeypatch):
    saved = []

    async def save_client(client_id, info):
        saved.append(info)

    monkeypatch.setattr(oauth, "save_client", save_client)
    body = {"redirect_uris": ["http://localhost/cb"], "token_endpoint_auth_method": "none"}

    response = client.post("/register", json=body)

    assert response.status_code == 201
    assert len(saved) == 1


def test_an_app_gets_its_tokens_with_redis_down(down):
    request = Request({"type": "http", "headers": [], "client": ("1.2.3.4", 1)})

    assert asyncio.run(oauth_limits.token_refusal(request, "c1")) is None


def test_an_apps_calls_go_on_with_redis_down(down):
    assert asyncio.run(mcp_tools.count_call("ann")) is None


def test_an_apps_call_isnt_failed_when_its_use_cant_be_recorded(down, monkeypatch):
    tracked = []

    async def used(grant_id, now):
        pass

    async def track(*args, **kwargs):
        tracked.append(args)

    monkeypatch.setattr(oauth, "used", used)
    monkeypatch.setattr(mcp_tools, "track", track)

    asyncio.run(mcp_tools.mark_active(ACCESS))

    assert tracked == []
