import pytest
from fake_redis import FakeRedis
from prepza_common.auth import current_user
from prepza_common.user import User

from app.main import app
from app.routers import superadmin


@pytest.fixture
def sign_in(monkeypatch):
    """Signs in as the email given; ann@example.com is a superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def signed_in(email):
        user = User(uid=email, email=email, email_verified=True, sign_in_provider="google.com")
        app.dependency_overrides[current_user] = lambda: user

    yield signed_in

    app.dependency_overrides.clear()


def test_a_superadmin_reads_how_much_of_the_shared_budgets_is_used_today(
    client, sign_in, monkeypatch
):
    redis = FakeRedis({"TOKENS_PER_DAY": 5_000_000})
    redis.counts.update({"spend:assistant:all": 1_250_000, "rate:assistant:all": 40})
    monkeypatch.setattr(superadmin, "get_redis", lambda: redis)
    sign_in("ann@example.com")

    response = client.get("/superadmin/budgets")

    assert response.status_code == 200
    assert [
        (budget["name"], budget["used"], budget["limit"], budget["unit"])
        for budget in response.json()
    ] == [
        ("TOKENS_PER_DAY", 1_250_000, 5_000_000, "tokens"),
        ("MESSAGES_PER_DAY", 40, 20_000, "calls"),
    ]
    assert response.json()[0]["share"] == 0.25


def test_the_budgets_are_hidden_from_everyone_else(client, sign_in, monkeypatch):
    monkeypatch.setattr(superadmin, "get_redis", lambda: FakeRedis())
    sign_in("bob@example.com")

    response = client.get("/superadmin/budgets")

    assert (response.status_code, response.json()["detail"]) == (404, "Not found")


def test_the_budgets_are_refused_signed_out(client):
    # Not found, as for everyone else: the admin zone doesn't show it's there.
    assert client.get("/superadmin/budgets").status_code == 404
