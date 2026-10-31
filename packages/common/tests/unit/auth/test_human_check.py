import asyncio

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from testee_common.auth import human_check
from testee_common.http import http


def request(token=None):
    headers = [(b"x-human-check", token.encode())] if token else []

    return Request({"type": "http", "headers": headers, "client": ("203.0.113.5", 1)})


@pytest.fixture
def cloudflare(monkeypatch):
    """Cloudflare's siteverify, faked: which tokens it confirms, and what it was asked."""
    state = {"good": {"ok-token"}, "asked": [], "down": False}

    async def post(url, data, timeout):
        state["asked"].append(data)

        if state["down"]:
            raise httpx.ConnectError("down")

        if data["secret"] == "set-me":
            body = {"success": False, "error-codes": ["invalid-input-secret"]}
        else:
            body = {"success": data["response"] in state["good"]}

        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(http, "get_client", lambda: type("C", (), {"post": staticmethod(post)}))

    return state


def check(token, secret="s3cret"):
    asyncio.run(human_check.require_human(request(token), secret))


def test_a_confirmed_token_passes_and_is_checked_with_the_visitors_address(cloudflare):
    check("ok-token")

    assert cloudflare["asked"] == [
        {"secret": "s3cret", "response": "ok-token", "remoteip": "203.0.113.5"}
    ]


@pytest.mark.parametrize("token", [None, "bad-token"])
def test_a_missing_or_unconfirmed_token_is_refused(cloudflare, token):
    with pytest.raises(HTTPException) as refused:
        check(token)

    assert refused.value.status_code == 403
    assert refused.value.detail == human_check.HUMAN_CHECK_FAILED


def test_without_a_secret_or_with_cloudflare_down_everyone_passes(cloudflare):
    check(None, secret="")
    cloudflare["down"] = True
    check("any-token")

    assert len(cloudflare["asked"]) == 1


def test_a_secret_cloudflare_rejects_locks_nobody_out(cloudflare):
    # Terraform's placeholder until the real secret is set.
    check("any-token", secret="set-me")
