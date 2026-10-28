import logging
from types import SimpleNamespace

import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from library.constants.emails import ADMIN_CANT_CONSENT, DEFAULTS
from library.main import app
from library.repositories import emails

ACCOUNT = SimpleNamespace(uid="ann", email="ann@example.com")
# A company's guest candidate: an account without an address.
GUEST = SimpleNamespace(uid="guest-1", email=None)


@pytest.fixture
def signed_in(monkeypatch):
    """Firebase knows Ann; storage records the changes. Signs in as the superadmin Sam, or as
    `email`."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    asked = []
    changes = []

    def get_user_by_email(email):
        asked.append(email)

        if email != ACCOUNT.email:
            raise firebase_auth.UserNotFoundError("none")

        return ACCOUNT

    def get_user(uid):
        if uid == GUEST.uid:
            return GUEST

        if uid != ACCOUNT.uid:
            raise firebase_auth.UserNotFoundError("none")

        return ACCOUNT

    async def preferences(user_id):
        return dict(DEFAULTS)

    async def change(user_id, settings, source, changed_by=None):
        changes.append((user_id, settings, source, changed_by))

        return {**DEFAULTS, **settings}

    monkeypatch.setattr(firebase_auth, "get_user_by_email", get_user_by_email)
    monkeypatch.setattr(firebase_auth, "get_user", get_user)
    monkeypatch.setattr(emails, "preferences", preferences)
    monkeypatch.setattr(emails, "change", change)

    def sign_in(email="sam@prepza.dev"):
        app.dependency_overrides[current_user] = lambda: User(
            uid="sam",
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    sign_in()
    yield SimpleNamespace(asked=asked, changes=changes, sign_in=sign_in)

    app.dependency_overrides.clear()


def test_a_superadmin_finds_an_account_by_its_address_whatever_its_case(client, signed_in):
    response = client.post("/superadmin/emails/lookup", json={"email": " Ann@Example.COM "})

    assert response.status_code == 200
    assert response.json() == {
        "account": {"user_id": "ann", "email": "ann@example.com", "preferences": DEFAULTS}
    }
    assert signed_in.asked == ["ann@example.com"]


def test_an_address_without_an_account_finds_none(client, signed_in):
    response = client.post("/superadmin/emails/lookup", json={"email": "zoe@example.com"})

    assert response.json() == {"account": None}


def test_a_superadmin_opens_an_accounts_email_settings_by_its_id(client, signed_in, caplog):
    with caplog.at_level(logging.INFO):
        response = client.get("/superadmin/emails/accounts/ann")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "ann",
        "email": "ann@example.com",
        "preferences": DEFAULTS,
    }
    assert "user ann viewed by superadmin sam" in caplog.text
    assert "ann@example.com" not in caplog.text


@pytest.mark.parametrize("user_id", ["gone", "guest-1"])
def test_an_id_without_an_account_to_email_is_not_found(client, signed_in, user_id):
    assert client.get(f"/superadmin/emails/accounts/{user_id}").status_code == 404


def test_text_that_cannot_be_an_address_finds_no_account(client, signed_in, monkeypatch):
    def invalid(email):
        raise ValueError("Malformed email address string")

    monkeypatch.setattr(firebase_auth, "get_user_by_email", invalid)
    response = client.post("/superadmin/emails/lookup", json={"email": "ann@ example"})

    assert response.json() == {"account": None}


def test_a_superadmins_change_is_logged_with_the_admin_source_and_their_id(
    client, signed_in, caplog
):
    off = {"updates": False, "promotions": False}

    with caplog.at_level(logging.WARNING):
        response = client.put("/superadmin/emails/ann/preferences", json={"changes": off})

    assert response.status_code == 200
    assert response.json() == {**DEFAULTS, **off}
    assert signed_in.changes == [("ann", off, "admin", "sam")]
    assert "changed by superadmin sam" in caplog.text


def test_a_change_to_an_account_that_is_gone_is_not_found(client, signed_in):
    response = client.put(
        "/superadmin/emails/gone/preferences", json={"changes": {"updates": False}}
    )

    assert response.status_code == 404
    assert signed_in.changes == []


@pytest.mark.parametrize("changes", [{"updates": True}, {"promotions": True, "reminders": False}])
def test_a_superadmin_cannot_turn_marketing_on_for_someone(client, signed_in, changes):
    """Consent to marketing is the user's own; turning the digest or reminders back on isn't
    marketing, so it stays allowed."""
    response = client.put("/superadmin/emails/ann/preferences", json={"changes": changes})

    assert response.status_code == 422
    assert response.json()["detail"] == ADMIN_CANT_CONSENT
    assert signed_in.changes == []
    assert (
        client.put(
            "/superadmin/emails/ann/preferences", json={"changes": {"reminders": True}}
        ).status_code
        == 200
    )


@pytest.mark.parametrize("changes", [{}, {"newsletter": False}])
def test_a_change_names_known_settings(client, signed_in, changes):
    response = client.put("/superadmin/emails/ann/preferences", json={"changes": changes})

    assert response.status_code == 422


def test_anyone_else_gets_not_found(client, signed_in):
    signed_in.sign_in("bob@example.com")

    lookup = client.post("/superadmin/emails/lookup", json={"email": "ann@example.com"})
    change = client.put("/superadmin/emails/ann/preferences", json={"changes": {"updates": False}})
    account = client.get("/superadmin/emails/accounts/ann")

    assert (lookup.status_code, change.status_code, account.status_code) == (404, 404, 404)
    assert (signed_in.asked, signed_in.changes) == ([], [])


def test_signed_out_gets_404_as_everyone_else(client):
    assert client.post("/superadmin/emails/lookup", json={"email": "a@b.c"}).status_code == 404
