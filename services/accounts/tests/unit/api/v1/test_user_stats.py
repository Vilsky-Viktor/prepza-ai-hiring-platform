from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from accounts.main import app


def account(year, month, day, uid="user"):
    made = datetime(year, month, day, tzinfo=UTC).timestamp() * 1000

    return SimpleNamespace(uid=uid, user_metadata=SimpleNamespace(creation_timestamp=made))


@pytest.fixture
def accounts(monkeypatch):
    """Four accounts in Firebase, and a company's guest candidate who has none of their own;
    signed in as Sam, the only superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    made = [
        account(2025, 12, 31),
        account(2026, 10, 1),
        account(2026, 10, 31),
        account(2026, 11, 1),
        account(2026, 10, 2, uid="guest-1"),
    ]
    listed = SimpleNamespace(iterate_all=lambda: iter(made))
    monkeypatch.setattr(firebase_auth, "list_users", lambda: listed)
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@prepza.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )

    yield

    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "query, users", [("", 4), ("?period=2026", 3), ("?period=2026-10", 2), ("?period=2025-11", 0)]
)
def test_the_stats_count_users_who_signed_up_in_the_period(client, accounts, query, users):
    response = client.get(f"/superadmin/stats{query}")

    assert response.json()["counts"] == {"users": users}


def test_only_a_superadmin_sees_the_stats(client, accounts):
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.get("/superadmin/stats").status_code == 404
