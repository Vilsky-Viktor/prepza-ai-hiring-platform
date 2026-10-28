"""Rounds' old help knowledge route, kept one release: it makes the same call to site, signed
with site's key, and answers what site answers."""

import httpx
import jwt
import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.http import http
from prepza_common.http.http import bearer

SECRET = "test-secret-that-is-at-least-32-bytes"
FROM_ASSISTANT = bearer(issue_token("assistant", "rounds", SECRET))


@pytest.fixture
def site(monkeypatch):
    """Site, answering each call with `answer` (status, body) and keeping what it got."""
    got = []
    answer = {"status": 200, "body": {"knowledge": "guide", "page_guide": None}}

    def reply(request):
        claims = jwt.decode(
            request.headers["authorization"].removeprefix("Bearer "),
            SECRET,
            algorithms=["HS256"],
            audience="site",
        )
        got.append((request.method, str(request.url), claims["iss"]))

        return httpx.Response(answer["status"], json=answer["body"])

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return got, answer


def test_the_knowledge_comes_from_site_with_its_query(client, site):
    got, _ = site

    response = client.get(
        "/internal/help/knowledge?country=DE&page=candidate", headers=FROM_ASSISTANT
    )

    assert (response.status_code, response.json()) == (
        200,
        {"knowledge": "guide", "page_guide": None},
    )
    assert got == [
        ("GET", "http://site/internal/help/knowledge?country=DE&page=candidate", "rounds")
    ]


def test_site_failing_is_answered_as_it_is(client, site):
    _, answer = site
    answer.update(status=503, body={"detail": "Unavailable"})

    assert client.get("/internal/help/knowledge", headers=FROM_ASSISTANT).status_code == 503


def test_a_call_without_rounds_key_reaches_nobody(client, site):
    got, _ = site

    assert client.get("/internal/help/knowledge").status_code == 401
    assert got == []
