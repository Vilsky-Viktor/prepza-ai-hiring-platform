import pytest
from prepza_common.auth.auth import current_user, optional_user
from prepza_common.auth.user import User

from billing.api.v1 import company_auto_top_ups, company_payments
from billing.main import app
from billing.repositories import company_actions, currencies, ledger, purchases
from billing.services import checkout_calls


@pytest.fixture(autouse=True)
def wallets_exist(monkeypatch):
    """Unit tests have no database: every owner's wallet exists unless a test says otherwise."""

    async def wallets(session, owner_type, owner_ids):
        return {owner_id: object() for owner_id in owner_ids}

    monkeypatch.setattr(ledger, "wallets", wallets)


@pytest.fixture(autouse=True)
def no_action_log(monkeypatch):
    """Unit tests have no database: a member's top-up isn't added to the action log (the
    integration tests check it is)."""

    def log_top_up(session, company_id, buyer_id):
        return None

    monkeypatch.setattr(purchases, "log_top_up", log_top_up)


@pytest.fixture(autouse=True)
def saved_currencies(monkeypatch):
    """Unit tests have no database: the currencies saved, by (owner type, id), in memory."""
    saved = {}

    async def chosen(session, owner_type, owner_id):
        return saved.get((owner_type, owner_id))

    async def choose(session, owner_type, owner_id, currency):
        saved[(owner_type, owner_id)] = currency

    async def remember(session, owner_type, owner_id, currency):
        return saved.setdefault((owner_type, owner_id), currency)

    async def forget(session, owner_type, owner_id):
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


@pytest.fixture
def editor(monkeypatch):
    """Signs in as the user given, an owner or admin of every company, for a company's payment
    routes; the access check and the count of calls to Paddle have their own tests
    (test_company_payments.py, test_company_auto_top_ups.py), and the action log's lines the
    integration tests'."""

    async def allowed(*args, **kwargs):
        return None

    for module in (company_auto_top_ups, company_payments):
        monkeypatch.setattr(module, "require", allowed)

    monkeypatch.setattr(checkout_calls, "count", allowed)
    monkeypatch.setattr(company_actions, "log", lambda *args: None)

    def sign_in(user_id):
        app.dependency_overrides[current_user] = lambda: User(
            uid=user_id, email=f"{user_id}@example.com", email_verified=True
        )

    yield sign_in
    app.dependency_overrides.clear()
