from firebase_admin import auth as firebase_auth

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


def test_me_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setattr(firebase_auth, "verify_id_token", fake_verify)

    response = client.get("/me", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/me")

    assert response.status_code == 401
