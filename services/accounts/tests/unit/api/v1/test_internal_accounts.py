"""Companies asks who an account id or an address belongs to, for the admin zone's support tab,
and how notes' authors show themselves; Firebase faked."""

from types import SimpleNamespace

import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.http.http import bearer

from accounts.constants.emails import FIREBASE_LOOKUP_LIMIT
from accounts.core.security import service_token

AUTH = bearer(service_token("accounts"))
ANN = SimpleNamespace(
    uid="ann",
    email="ann@example.com",
    # Firebase keeps it in milliseconds: 2026-10-01T00:00:00Z.
    user_metadata=SimpleNamespace(creation_timestamp=1_790_812_800_000),
)
GUEST = SimpleNamespace(uid="guest-1", email=None, user_metadata=None)
FOUND = {"user_id": "ann", "email": "ann@example.com", "created_at": "2026-10-01T00:00:00Z"}


@pytest.fixture(autouse=True)
def firebase(monkeypatch):
    """Ann and a guest; the addresses asked for are kept."""
    asked = []
    accounts = {ANN.uid: ANN, GUEST.uid: GUEST}

    def get_user(uid):
        if len(uid) > 128:
            raise ValueError("Invalid uid")

        if uid not in accounts:
            raise firebase_auth.UserNotFoundError("none")

        return accounts[uid]

    def get_user_by_email(email):
        asked.append(email)

        if email != ANN.email:
            raise firebase_auth.UserNotFoundError("none")

        return ANN

    monkeypatch.setattr(firebase_auth, "get_user", get_user)
    monkeypatch.setattr(firebase_auth, "get_user_by_email", get_user_by_email)

    return asked


def test_an_account_by_its_id_with_its_address_and_when_it_was_made(client):
    response = client.get("/internal/accounts/ann", headers=AUTH)

    assert (response.status_code, response.json()) == (200, FOUND)
    assert client.get("/internal/accounts/guest-1", headers=AUTH).json() == {
        "user_id": "guest-1",
        "email": None,
        "created_at": None,
    }


@pytest.mark.parametrize("user_id", ["gone", "x" * 200])
def test_an_id_without_an_account_is_not_found(client, user_id):
    assert client.get(f"/internal/accounts/{user_id}", headers=AUTH).status_code == 404


def test_an_account_by_its_address_whatever_its_case(client, firebase):
    response = client.post(
        "/internal/accounts/lookup", json={"email": " Ann@Example.com "}, headers=AUTH
    )
    gone = client.post("/internal/accounts/lookup", json={"email": "zoe@example.com"}, headers=AUTH)

    assert (response.status_code, response.json()) == (200, FOUND)
    assert gone.status_code == 404
    assert firebase == ["ann@example.com", "zoe@example.com"]


def test_profiles_give_each_accounts_name_or_email_and_leave_out_those_gone(client, monkeypatch):
    named = SimpleNamespace(
        uid="ann", display_name="Ann Lee", email="ann@example.com", photo_url="https://x/ann.png"
    )
    unnamed = SimpleNamespace(uid="bob", display_name=None, email="bob@example.com", photo_url=None)
    asked = []

    def get_users(identifiers):
        asked.append([item.uid for item in identifiers])

        return SimpleNamespace(users=[named, unnamed])

    monkeypatch.setattr(firebase_auth, "get_users", get_users)

    response = client.post(
        "/internal/accounts/profiles", json={"user_ids": ["ann", "bob", "gone"]}, headers=AUTH
    )

    assert response.json() == {
        "profiles": [
            {"user_id": "ann", "name": "Ann Lee", "photo_url": "https://x/ann.png"},
            {"user_id": "bob", "name": "bob@example.com", "photo_url": None},
        ]
    }
    assert asked == [["ann", "bob", "gone"]]


def test_profiles_of_no_ids_ask_firebase_nothing_and_of_too_many_are_refused(client, monkeypatch):
    def get_users(identifiers):
        raise AssertionError("Firebase asked")

    monkeypatch.setattr(firebase_auth, "get_users", get_users)
    url = "/internal/accounts/profiles"
    too_many = [f"user-{index}" for index in range(FIREBASE_LOOKUP_LIMIT + 1)]

    assert client.post(url, json={"user_ids": []}, headers=AUTH).json() == {"profiles": []}
    assert client.post(url, json={"user_ids": too_many}, headers=AUTH).status_code == 422
    assert client.post(url, json={"user_ids": ["ann"]}).status_code == 401
