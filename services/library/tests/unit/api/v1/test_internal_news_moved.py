"""Library's old internal news routes, kept one release: each makes the same call to site, signed
with site's key, and answers what site answers."""

import httpx
import jwt
import pytest
from prepza_common.http import http
from prepza_common.http.http import bearer

from tests.unit.api.v1.test_internal import token

AUTH = bearer(token())
SECRET = "test-secret-that-is-at-least-32-bytes"


@pytest.fixture
def site(monkeypatch):
    """Site, answering each call with `answer` (status, body) and keeping what it got."""
    got = []
    answer = {"status": 200, "body": {"titles": {"n1": "Hello"}}}

    def reply(request):
        claims = jwt.decode(
            request.headers["authorization"].removeprefix("Bearer "),
            SECRET,
            algorithms=["HS256"],
            audience="site",
        )
        got.append((request.method, str(request.url), request.content, claims["iss"]))

        return httpx.Response(answer["status"], json=answer["body"])

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return got, answer


def test_the_bells_titles_come_from_site_with_the_body(client, site):
    got, _ = site
    body = {"news_ids": ["n1"], "language": "de"}

    response = client.post("/internal/news/titles", json=body, headers=AUTH)

    assert (response.status_code, response.json()) == (200, {"titles": {"n1": "Hello"}})
    assert got == [
        (
            "POST",
            "http://site:8000/internal/news/titles",
            b'{"news_ids":["n1"],"language":"de"}',
            "library",
        )
    ]


def test_a_deleted_post_is_answered_as_site_answers(client, site):
    _, answer = site
    answer.update(status=404, body={"detail": "Not found"})

    response = client.get("/internal/news/n1", headers=AUTH)

    assert (response.status_code, response.json()) == (404, {"detail": "Not found"})


def test_translations_go_to_site(client, site):
    got, _ = site

    client.put("/internal/news/n1/translations", json={"title": "T"}, headers=AUTH)

    assert got[0][:2] == ("PUT", "http://site:8000/internal/news/n1/translations")


def test_a_call_without_librarys_key_reaches_nobody(client, site):
    got, _ = site

    assert client.post("/internal/news/titles", json={}).status_code == 401
    assert got == []
