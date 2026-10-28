"""Library's old account routes, kept one release: each makes the same call to accounts, signed
with accounts' key, and answers what accounts answers."""

import httpx
import jwt
import pytest
from prepza_common.http import http
from prepza_common.http.http import bearer

from tests.unit.api.v1.test_internal import token

AUTH = bearer(token())
SECRET = "test-secret-that-is-at-least-32-bytes"


@pytest.fixture
def accounts(monkeypatch):
    """Accounts, answering each call with `answer` (status, body) and keeping what it got."""
    got = []
    answer = {"status": 200, "body": {"user_ids": ["ann"]}}

    def reply(request):
        claims = jwt.decode(
            request.headers["authorization"].removeprefix("Bearer "),
            SECRET,
            algorithms=["HS256"],
            audience="accounts",
        )
        got.append((request.method, str(request.url), request.content, claims["iss"]))

        return httpx.Response(answer["status"], json=answer["body"])

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(http, "get_client", lambda: client)

    return got, answer


def test_a_read_goes_to_accounts_with_its_query(client, accounts):
    got, _ = accounts

    response = client.get("/internal/users/ids?after=a&setting=updates", headers=AUTH)

    assert (response.status_code, response.json()) == (200, {"user_ids": ["ann"]})
    assert got == [
        ("GET", "http://accounts:8000/internal/users/ids?after=a&setting=updates", b"", "library")
    ]


def test_a_write_goes_to_accounts_with_its_body(client, accounts):
    got, _ = accounts

    client.post("/internal/users/ann/unsubscribe", json={"settings": ["updates"]}, headers=AUTH)

    assert got == [
        (
            "POST",
            "http://accounts:8000/internal/users/ann/unsubscribe",
            b'{"settings":["updates"]}',
            "library",
        )
    ]


def test_accounts_not_finding_the_account_is_answered_as_it_is(client, accounts):
    _, answer = accounts
    answer.update(status=404, body={"detail": "Not found"})

    response = client.post("/internal/accounts/lookup", json={"email": "a@b.co"}, headers=AUTH)

    assert (response.status_code, response.json()) == (404, {"detail": "Not found"})


def test_a_call_without_librarys_key_reaches_nobody(client, accounts):
    got, _ = accounts

    assert client.get("/internal/accounts/ann").status_code == 401
    assert got == []
