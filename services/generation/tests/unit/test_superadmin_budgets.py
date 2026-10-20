import pytest
from prepza_common.auth import current_user
from prepza_common.limit_list import LIMITS
from prepza_common.user import User

from app.constants.generation import BUDGET_KEY
from app.main import app
from app.services.budget import day_key


@pytest.fixture
def signed_in(monkeypatch):
    """Signs someone in; Ann is the only superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid="u1",
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in

    app.dependency_overrides.clear()


def test_a_superadmin_sees_how_much_of_each_shared_budget_is_used_today(client, redis, signed_in):
    redis.limits["DAILY_GENERATION_LIMIT"] = "40"
    redis.counts[day_key(BUDGET_KEY)] = 10
    signed_in("ann@example.com")

    response = client.get("/superadmin/budgets")

    assert response.status_code == 200
    by_name = {budget["name"]: budget for budget in response.json()}
    assert by_name["DAILY_GENERATION_LIMIT"] == {
        "name": "DAILY_GENERATION_LIMIT",
        "used": 10,
        "limit": 40,
        "unit": LIMITS["DAILY_GENERATION_LIMIT"].unit,
        "share": 0.25,
    }
    # Nothing used yet today, at its default.
    verify = by_name["DAILY_VERIFY_LIMIT"]
    assert (verify["used"], verify["limit"]) == (0, LIMITS["DAILY_VERIFY_LIMIT"].default)
    # Reading the budgets counts nothing.
    assert list(redis.counts) == [day_key(BUDGET_KEY)]


def test_anyone_else_cant(client, signed_in):
    signed_in("eve@example.com")

    assert client.get("/superadmin/budgets").status_code == 404
