from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from prepza_common.service_auth import (
    callee_secret,
    issue_token,
    only_from,
    service_caller,
    token_caller,
    token_claims,
)

LIBRARY_SECRET = "library-secret-that-is-at-least-32-bytes"
ROUNDS_SECRET = "rounds-secret-that-is-at-least-32-bytes!"


def library():
    """Library's app, admitting calls signed with its key and addressed to it."""
    app = FastAPI()
    caller = service_caller(LIBRARY_SECRET, "library")

    @app.get("/internal")
    def internal(name: caller) -> dict:
        return {"caller": name}

    return TestClient(app)


def call(token):
    return library().get("/internal", headers={"Authorization": f"Bearer {token}"})


def test_a_token_for_library_signed_with_its_key_names_the_caller():
    response = call(issue_token("companies", "library", LIBRARY_SECRET))

    assert response.status_code == 200
    assert response.json() == {"caller": "companies"}


@pytest.mark.parametrize(
    "token",
    [
        # Addressed to rounds: useless at library, even with library's key.
        issue_token("companies", "rounds", LIBRARY_SECRET),
        # Signed with another service's key.
        issue_token("companies", "library", ROUNDS_SECRET),
        jwt.encode(
            {"iss": "companies", "aud": "library", "exp": datetime.now(UTC) - timedelta(seconds=1)},
            LIBRARY_SECRET,
            algorithm="HS256",
        ),
        # The old kind of token, without an audience.
        jwt.encode(
            {"iss": "companies", "exp": datetime.now(UTC) + timedelta(seconds=30)},
            LIBRARY_SECRET,
            algorithm="HS256",
        ),
    ],
    ids=["for another service", "wrong key", "expired", "no audience"],
)
def test_other_tokens_are_refused(token):
    assert call(token).status_code == 401


def test_a_caller_reads_the_key_of_the_service_it_calls(monkeypatch):
    monkeypatch.setenv("LIBRARY_SERVICE_SECRET", LIBRARY_SECRET)

    assert callee_secret("library") == LIBRARY_SECRET


def test_a_token_is_checked_without_a_request():
    assert (
        token_caller(issue_token("assistant", "library", LIBRARY_SECRET), LIBRARY_SECRET, "library")
        == "assistant"
    )
    assert (
        token_caller(issue_token("assistant", "library", ROUNDS_SECRET), LIBRARY_SECRET, "library")
        is None
    )
    assert token_caller("not a token", LIBRARY_SECRET, "library") is None


def test_extra_claims_ride_along_signed_and_never_replace_the_callers():
    extra = {"company": "c1", "iss": "library"}
    token = issue_token("assistant", "library", LIBRARY_SECRET, extra)

    claims = token_claims(token, LIBRARY_SECRET, "library")

    assert claims["company"] == "c1"
    assert claims["iss"] == "assistant"
    assert token_claims(token, ROUNDS_SECRET, "library") is None


def test_only_from_lets_the_allowed_caller_through():
    assert only_from("assistant", "assistant") is None


def test_only_from_refuses_another_caller():
    with pytest.raises(HTTPException) as refused:
        only_from("library", "assistant")

    assert refused.value.status_code == 403
    assert refused.value.detail == "Not allowed"
