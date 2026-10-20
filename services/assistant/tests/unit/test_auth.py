import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth

from app.auth import user_with_token


def credentials(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# A message to the assistant, which writes.
POST = Request({"type": "http", "method": "POST", "headers": []})


def test_a_signed_in_user_comes_with_their_raw_token(monkeypatch):
    claims = {"uid": "u1", "email": "ann@example.com"}
    monkeypatch.setattr(firebase_auth, "verify_id_token", lambda token, **_: claims)

    user, token = user_with_token(POST, credentials("raw-id-token"))

    assert (user.uid, user.email, token) == ("u1", "ann@example.com", "raw-id-token")


def test_an_invalid_token_is_refused(monkeypatch):
    def invalid(token, **_):
        raise firebase_auth.InvalidIdTokenError("bad")

    monkeypatch.setattr(firebase_auth, "verify_id_token", invalid)

    with pytest.raises(HTTPException) as error:
        user_with_token(POST, credentials("forged"))

    assert error.value.status_code == 401


def test_the_service_starts_with_its_tools_and_answers_health(client):
    assert client.get("/health").json() == {"status": "ok"}
