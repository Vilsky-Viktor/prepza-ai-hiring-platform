import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.http.http import bearer

from library.constants.emails import DEFAULTS
from library.main import app
from library.repositories import emails
from tests.unit.api.v1.test_internal import token

USER = User(uid="ann", email="ann@example.com", email_verified=True, name="Ann")


@pytest.fixture
def signed_in(monkeypatch):
    """Ann is signed in; returns the changes the routes pass to storage."""
    calls = []

    async def preferences(user_id):
        return dict(DEFAULTS)

    async def change(user_id, changes, source):
        calls.append((user_id, changes, source))

        return {**DEFAULTS, **changes}

    monkeypatch.setattr(emails, "preferences", preferences)
    monkeypatch.setattr(emails, "change", change)
    app.dependency_overrides[current_user] = lambda: USER
    yield calls

    app.dependency_overrides.clear()


def test_a_new_user_gets_activity_and_reminders_but_no_marketing(client, signed_in):
    response = client.get("/me/email-preferences")

    assert response.status_code == 200
    assert response.json() == {
        "candidate_finished": True,
        "invite_undelivered": True,
        "ats_not_invited": True,
        "interview_ready": True,
        "reminders": True,
        "updates": False,
        "promotions": False,
    }


def test_settings_change_any_setting_either_way(client, signed_in):
    body = {"changes": {"reminders": False, "updates": True}, "source": "settings"}

    response = client.put("/me/email-preferences", json=body)

    assert response.status_code == 200
    assert response.json()["reminders"] is False
    assert response.json()["updates"] is True
    assert signed_in == [("ann", {"reminders": False, "updates": True}, "settings")]


@pytest.mark.parametrize(
    "changes",
    [
        {"updates": True, "promotions": True},
        # The updates opt-out was ticked.
        {"updates": False},
    ],
)
def test_signing_in_sets_updates_and_turns_on_promotions(client, signed_in, changes):
    body = {"changes": changes, "source": "sign_in"}

    assert client.put("/me/email-preferences", json=body).status_code == 200
    assert signed_in == [("ann", changes, "sign_in")]


@pytest.mark.parametrize(
    "body",
    [
        # Signing in never turns promotions off, nor touches anything but marketing.
        {"changes": {"promotions": False}, "source": "sign_in"},
        {"changes": {"reminders": True}, "source": "sign_in"},
        # Unsubscribing has its own way in.
        {"changes": {"updates": False}, "source": "unsubscribe"},
        {"changes": {"newsletter": True}, "source": "settings"},
        {"changes": {}, "source": "settings"},
    ],
)
def test_refused_changes_change_nothing(client, signed_in, body):
    assert client.put("/me/email-preferences", json=body).status_code == 422
    assert signed_in == []


def test_preferences_need_a_sign_in(client):
    assert client.get("/me/email-preferences").status_code == 401


def test_notifications_unsubscribes_a_user_from_an_email_link(client, signed_in):
    response = client.post(
        "/internal/users/ann/unsubscribe",
        json={"settings": ["candidate_finished", "interview_ready"]},
        headers=bearer(token()),
    )

    assert response.status_code == 200
    assert response.json()["interview_ready"] is False
    assert signed_in == [
        ("ann", {"candidate_finished": False, "interview_ready": False}, "unsubscribe")
    ]


@pytest.mark.parametrize("settings", [[], ["newsletter"]])
def test_an_unsubscribe_names_known_settings(client, signed_in, settings):
    response = client.post(
        "/internal/users/ann/unsubscribe",
        json={"settings": settings},
        headers=bearer(token()),
    )

    assert response.status_code == 422
    assert signed_in == []


def test_only_services_unsubscribe_a_user(client, signed_in):
    response = client.post("/internal/users/ann/unsubscribe", json={"settings": ["updates"]})

    assert response.status_code == 401
