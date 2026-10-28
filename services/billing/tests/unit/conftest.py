import pytest
from prepza_common.auth.auth import current_user, optional_user
from prepza_common.auth.user import User

from billing.main import app
from billing.repositories import currencies, ledger


@pytest.fixture(autouse=True)
def wallets_exist(monkeypatch):
    """Unit tests have no database: every owner's wallet exists unless a test says otherwise."""

    async def wallets(owner_type, owner_ids):
        return {owner_id: object() for owner_id in owner_ids}

    monkeypatch.setattr(ledger, "wallets", wallets)


@pytest.fixture(autouse=True)
def saved_currencies(monkeypatch):
    """Unit tests have no database: the currencies saved, by (owner type, id), in memory."""
    saved = {}

    async def chosen(owner_type, owner_id):
        return saved.get((owner_type, owner_id))

    async def choose(owner_type, owner_id, currency):
        saved[(owner_type, owner_id)] = currency

    async def remember(owner_type, owner_id, currency):
        return saved.setdefault((owner_type, owner_id), currency)

    async def forget(owner_type, owner_id):
        saved.pop((owner_type, owner_id), None)

    for name, fake in (
        ("chosen", chosen),
        ("choose", choose),
        ("remember", remember),
        ("forget", forget),
    ):
        monkeypatch.setattr(currencies, name, fake)

    return saved


@pytest.fixture
def signed_in(monkeypatch):
    """Signs in as the email given; ann@example.com is a superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        user = User(uid=email, email=email, email_verified=True, sign_in_provider="google.com")
        app.dependency_overrides[current_user] = lambda: user
        app.dependency_overrides[optional_user] = lambda: user

    yield sign_in
    app.dependency_overrides.clear()
