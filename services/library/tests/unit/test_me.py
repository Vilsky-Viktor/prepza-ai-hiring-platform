from types import SimpleNamespace

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


def test_me_says_whether_the_user_is_an_admin(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    assert client.get("/me", headers=AUTH).json()["is_superadmin"] is True


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

    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)
    monkeypatch.setattr(
        firebase_auth, "get_user", lambda uid: SimpleNamespace(custom_claims=claims)
    )
    monkeypatch.setattr(
        firebase_auth, "set_custom_user_claims", lambda uid, claims: stored.update({uid: claims})
    )
    monkeypatch.setattr(accounts, "track", track)
    monkeypatch.setattr(legal, "accept_terms", accept_terms)

    return stored, tracked


def test_settings_store_the_language_on_the_sign_in(client, monkeypatch):
    stored, tracked = settings_with(monkeypatch, {"language": "en"})

    response = client.put("/me/settings", json={"language": "ru"}, headers=AUTH)

    assert response.status_code == 204
    assert stored == {"user-1": {"language": "ru"}}
    assert tracked == []


def test_a_new_accounts_first_language_counts_as_signing_up(client, monkeypatch):
    _, tracked = settings_with(monkeypatch, None)

    client.put("/me/settings", json={"language": "de"}, headers=AUTH)

    # Signing up accepts the terms in force: their version is kept.
    assert tracked == [
        ("terms", {"user_id": "user-1", "version": LEGAL_VERSIONS["terms"]}),
        ("signed_up", {"user_id": "user-1", "language": "de"}),
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
