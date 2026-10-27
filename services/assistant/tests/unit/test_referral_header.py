import asyncio

import httpx
import pytest
from prepza_common.http import http

from app.integrations import services


@pytest.fixture
def sent(monkeypatch):
    """The headers of each request the services get."""
    headers = []

    def handler(request):
        headers.append(dict(request.headers))

        return httpx.Response(201, json={})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return headers


@pytest.mark.parametrize(
    ("service", "referral", "cookie"),
    [
        ("companies", "abc_12-3", "prepza_ref=abc_12-3"),
        # Only companies reads it, and only a code that reads right is passed on.
        ("billing", "abc123", None),
        ("companies", "abc; other=1", None),
        ("companies", None, None),
    ],
)
def test_only_companies_gets_a_well_formed_referral_code(sent, service, referral, cookie):
    asyncio.run(services.send(service, "POST", "/x", {}, {}, "token", "en", referral=referral))

    assert sent[0].get("cookie") == cookie
