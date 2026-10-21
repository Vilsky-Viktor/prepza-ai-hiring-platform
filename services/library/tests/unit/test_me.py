from types import SimpleNamespace

import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.constants import LEGAL_VERSIONS

from app.services import accounts
from app.storage import legal

AUTH = {"Authorization": "Bearer good-token"}

CLAIMS = {
    "uid": "user-1",
    "email": "ann@example.com",
    "email_verified": True,
    "name": "Ann",
}


def fake_verify(token, **_):
    if token != "good-token":
        raise firebase_auth.InvalidIdTokenError("bad token")

    return CLAIMS


def test_me_returns_user_from_token(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)

    response = client.get("/me", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json() == {**CLAIMS, "language": "en", "is_superadmin": False}


def signed_in_with(provider):
    claims = {**CLAIMS, "firebase": {"sign_in_provider": provider}}

    return lambda token, **_: claims


def test_me_says_whether_the_user_is_an_admin(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", signed_in_with("google.com"))
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    body = client.get("/me", headers=AUTH).json()

    assert body["is_superadmin"] is True
    # How the user signed in stays with the services.
    assert "sign_in_provider" not in body


def test_an_admins_address_signed_in_with_github_isnt_one(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", signed_in_with("github.com"))
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    assert client.get("/me", headers=AUTH).json()["is_superadmin"] is False


def test_me_reads_the_language_from_the_token(client, monkeypatch):
    monkeypatch.setattr(
        firebase_auth, "verify_id_token", lambda token, **_: {**CLAIMS, "language": "ru"}
    )

    assert client.get("/me", headers=AUTH).json()["language"] == "ru"


def settings_with(monkeypatch, claims):
    """Stores the language as a sign-in with these claims; returns what was stored and tracked
    (the terms accepted among it)."""
    stored, tracked = {}, []

    async def track(event, **values):
        tracked.append((event, values))

    async def accept_terms(user_id, version):
        tracked.append(("terms", {"user_id": user_id, "version": version}))

    async def remember_currency(user_id, country):
        tracked.append(("currency", {"user_id": user_id, "country": country}))

    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)
    monkeypatch.setattr(
        firebase_auth, "get_user", lambda uid: SimpleNamespace(custom_claims=claims)
    )
    monkeypatch.setattr(
        firebase_auth, "set_custom_user_claims", lambda uid, claims: stored.update({uid: claims})
    )
    monkeypatch.setattr(accounts, "track", track)
    monkeypatch.setattr(legal, "accept_terms", accept_terms)
    monkeypatch.setattr(accounts, "remember_currency", remember_currency)

    return stored, tracked


def test_settings_store_the_language_on_the_sign_in(client, monkeypatch):
    stored, tracked = settings_with(monkeypatch, {"language": "en"})

    response = client.put("/me/settings", json={"language": "ru"}, headers=AUTH)

    assert response.status_code == 204
    assert stored == {"user-1": {"language": "ru"}}
    assert tracked == []


@pytest.mark.parametrize("country", [None, "FR"])
def test_a_new_accounts_first_language_counts_as_signing_up(client, monkeypatch, country):
    """Its currency is saved from the visitor's country, which calls without a browser (and
    tests) don't have: billing then saves none until it sees one."""
    _, tracked = settings_with(monkeypatch, None)
    headers = {**AUTH, "X-Client-Country": country} if country else AUTH

    assert client.put("/me/settings", json={"language": "de"}, headers=headers).status_code == 204

    # Signing up accepts the terms in force: their version is kept.
    assert tracked == [
        ("terms", {"user_id": "user-1", "version": LEGAL_VERSIONS["terms"]}),
        ("signed_up", {"user_id": "user-1", "language": "de"}),
        ("currency", {"user_id": "user-1", "country": country}),
    ]


def test_a_companys_guest_candidate_accepts_the_terms_but_isnt_a_sign_up(client, monkeypatch):
    _, tracked = settings_with(monkeypatch, None)
    monkeypatch.setitem(CLAIMS, "uid", "guest-1")
    monkeypatch.setitem(CLAIMS, "email", "")

    client.put("/me/settings", json={"language": "de"}, headers=AUTH)

    assert tracked == [("terms", {"user_id": "guest-1", "version": LEGAL_VERSIONS["terms"]})]


def test_settings_refuse_an_unknown_language(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)

    response = client.put("/me/settings", json={"language": "xx"}, headers=AUTH)

    assert response.status_code == 422


def test_me_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)

    response = client.get("/me", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/me")

    assert response.status_code == 401
