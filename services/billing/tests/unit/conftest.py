import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.main import app
from app.storage import ledger


@pytest.fixture(autouse=True)
def wallets_exist(monkeypatch):
    """Unit tests have no database: every owner's wallet exists unless a test says otherwise."""

    async def wallets(owner_type, owner_ids):
        return {owner_id: object() for owner_id in owner_ids}

    monkeypatch.setattr(ledger, "wallets", wallets)


@pytest.fixture
def signed_in(monkeypatch):
    """Signs in as the email given; ann@example.com is a superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid=email,
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in
    app.dependency_overrides.clear()
