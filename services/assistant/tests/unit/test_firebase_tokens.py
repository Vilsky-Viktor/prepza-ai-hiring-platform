import asyncio
import threading
from types import SimpleNamespace

import httpx
import pytest
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import ResourceExhaustedError
from prepza_common.auth.user import User
from prepza_common.http import http
from prepza_common.redis import memory_cache

from app.config.settings import settings
from app.constants.mcp import MAX_KEEP_SECONDS
from app.integrations import firebase_tokens

ANN = User(uid="ann", email="ann@example.com", email_verified=True, language="de")


@pytest.fixture
def firebase(monkeypatch):
    """Firebase's accounts and sign-in API: every sign-in posted."""
    signed = {"idToken": "id-token", "expiresIn": "3600"}
    state = SimpleNamespace(accounts={"ann": False}, posts=[], reply=(200, signed), lookup=None)

    def get_user(uid):
        if state.lookup is not None:
            raise state.lookup

        if uid not in state.accounts:
            raise firebase_auth.UserNotFoundError("gone")

        return SimpleNamespace(disabled=state.accounts[uid])

    class Client:
        async def post(self, url, params, json):
            state.posts.append((url, params, json))
            request = httpx.Request("POST", url)

            status, body = state.reply

            return httpx.Response(status, json=body, request=request)

    monkeypatch.setattr(firebase_auth, "get_user", get_user)
    monkeypatch.setattr(firebase_auth, "create_custom_token", lambda uid: b"custom")
    monkeypatch.setattr(http, "get_client", Client)
    monkeypatch.setattr(firebase_tokens, "verify", lambda token: ANN)
    firebase_tokens.forget("ann")

    yield state

    firebase_tokens.forget("ann")


def test_the_user_is_signed_in_with_a_custom_token_and_kept(firebase):
    first = asyncio.run(firebase_tokens.sign_in("ann"))
    again = asyncio.run(firebase_tokens.sign_in("ann"))

    assert first == again == (ANN, "id-token")
    [(url, params, body)] = firebase.posts
    assert url.endswith("/accounts:signInWithCustomToken")
    assert params == {"key": settings.firebase_web_api_key}
    assert body == {"token": "custom", "returnSecureToken": True}


def test_the_token_is_checked_off_the_event_loop(firebase, monkeypatch):
    threads = []

    def verify(token):
        threads.append(threading.current_thread())

        return ANN

    monkeypatch.setattr(firebase_tokens, "verify", verify)
    asyncio.run(firebase_tokens.sign_in("ann"))

    assert threads and threads[0] is not threading.main_thread()


def test_an_account_disabled_after_signing_in_loses_access_within_minutes(firebase, monkeypatch):
    clock = SimpleNamespace(now=1000.0)
    monkeypatch.setattr(memory_cache.time, "monotonic", lambda: clock.now)
    asyncio.run(firebase_tokens.sign_in("ann"))
    firebase.accounts["ann"] = True

    soon = asyncio.run(firebase_tokens.sign_in("ann"))
    clock.now += MAX_KEEP_SECONDS + 1
    later = asyncio.run(firebase_tokens.sign_in("ann"))

    assert soon == (ANN, "id-token")
    assert later is None


def test_forgetting_signs_in_again(firebase):
    asyncio.run(firebase_tokens.sign_in("ann"))
    firebase_tokens.forget("ann")
    asyncio.run(firebase_tokens.sign_in("ann"))

    assert len(firebase.posts) == 2
    assert memory_cache.get("mcp:id-token:ann") == (ANN, "id-token")


@pytest.mark.parametrize("disabled", [None, True], ids=["deleted", "disabled"])
def test_an_account_thats_gone_or_disabled_isnt_signed_in(firebase, disabled):
    if disabled is None:
        firebase.accounts.clear()
    else:
        firebase.accounts["ann"] = True

    assert asyncio.run(firebase_tokens.sign_in("ann")) is None
    # Never a custom token for an unknown account: it would create one.
    assert firebase.posts == []


def test_the_emulator_is_used_locally_and_google_otherwise(monkeypatch):
    monkeypatch.setattr(settings, "firebase_auth_emulator_host", "firebase-auth:9199")
    local = firebase_tokens.identity_url()
    monkeypatch.setattr(settings, "firebase_auth_emulator_host", "")

    assert local == "http://firebase-auth:9199/identitytoolkit.googleapis.com/v1"
    assert firebase_tokens.identity_url() == "https://identitytoolkit.googleapis.com/v1"


def refusals(published) -> list[tuple]:
    return [
        (data["limit"], data["kind"], data["user_id"])
        for kind, data in published
        if kind == "limit.hit"
    ]


@pytest.mark.parametrize(
    "status, body",
    [
        (429, {}),
        (400, {"error": {"message": "TOO_MANY_ATTEMPTS_TRY_LATER"}}),
        (400, {"error": {"message": "QUOTA_EXCEEDED : Exceeded quota"}}),
    ],
)
def test_firebase_refusing_a_sign_in_for_its_limits_is_recorded(firebase, published, status, body):
    firebase.reply = (status, body)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(firebase_tokens.sign_in("ann"))

    assert refusals(published) == [("FIREBASE_TOKEN_REFUSED", "provider:firebase", "ann")]


def test_firebase_refusing_a_bad_token_isnt_a_limit_hit(firebase, published):
    firebase.reply = (400, {"error": {"message": "INVALID_CUSTOM_TOKEN"}})

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(firebase_tokens.sign_in("ann"))

    assert refusals(published) == []


def test_firebase_out_of_quota_reading_the_account_is_recorded(firebase, published):
    firebase.lookup = ResourceExhaustedError("quota", None)

    with pytest.raises(ResourceExhaustedError):
        asyncio.run(firebase_tokens.sign_in("ann"))

    assert refusals(published) == [("FIREBASE_TOKEN_REFUSED", "provider:firebase", "ann")]
