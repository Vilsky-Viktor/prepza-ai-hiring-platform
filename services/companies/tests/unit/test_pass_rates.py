import uuid
from types import SimpleNamespace

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.helpers.pass_rates import outside_triggers, percent
from app.integrations import rounds
from app.main import app
from app.storage import pass_rates

SET_ID = uuid.uuid4()


def test_percent_rounds_and_has_none_without_a_whole():
    assert percent(1, 3) == 33
    assert percent(2, 3) == 67
    assert percent(0, 0) is None


def test_the_trigger_needs_twenty_finished_and_a_rate_below_10_or_above_95():
    # 19 finished: too few to judge, whatever the rate.
    assert not outside_triggers(0, 19)
    assert outside_triggers(1, 20)
    assert not outside_triggers(2, 20)
    assert not outside_triggers(19, 20)
    assert outside_triggers(20, 20)
    # 9.5% rounds to 10% on screen, but is still below the trigger.
    assert outside_triggers(19, 200)
    # Exactly 95% is inside.
    assert not outside_triggers(95, 100)


@pytest.fixture
def superadmin(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    yield
    app.dependency_overrides.clear()


def test_superadmin_sees_each_interviews_rates_with_its_timeouts(client, monkeypatch, superadmin):
    asked = {}

    async def page(by_finished, after, limit):
        asked["page"] = (by_finished, after, limit)
        row = SimpleNamespace(
            id=uuid.uuid4(),
            title="Backend",
            set_id=SET_ID,
            pass_mark=60,
            company="Acme",
            finished=20,
            passed=1,
            average=41.6,
        )

        return [row]

    async def answer_counts(set_ids):
        asked["sets"] = set_ids

        return {str(SET_ID): [3, 40]}

    monkeypatch.setattr(pass_rates, "page", page)
    monkeypatch.setattr(rounds, "answer_counts", answer_counts)

    after = uuid.uuid4()
    [row] = client.get(f"/superadmin/pass-rates?sort=finished&limit=10&after={after}").json()

    assert asked == {"page": (True, after, 10), "sets": [SET_ID]}
    assert row["finished"] == 20
    assert row["pass_rate"] == 5
    assert row["average_grade"] == 42
    assert row["timeout_share"] == 8
    assert row["outside_triggers"]


def test_pass_rates_are_not_found_for_others(client):
    app.dependency_overrides[current_user] = lambda: User(
        uid="eve",
        email="eve@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.get("/superadmin/pass-rates").status_code == 404

    app.dependency_overrides.clear()
