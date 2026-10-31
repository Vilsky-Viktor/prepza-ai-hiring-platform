from datetime import UTC, datetime, timedelta

import httpx
import pytest
from testee_common.auth.auth import current_user, optional_user
from testee_common.auth.user import User

from companies.api.v1 import maintenance as maintenance_routes
from companies.main import app

ANN = User(uid="ann", email="ann@example.com", email_verified=True, sign_in_provider="google.com")
BOB = User(uid="bob", email="bob@example.com", email_verified=True, sign_in_provider="google.com")


@pytest.fixture(autouse=True)
def switch(monkeypatch):
    """The switch in memory, on for an hour, ann a superadmin and rounds counting 2; returns the
    turns made and the time given back to running interviews."""
    state = {"on": True, "started": datetime.now(UTC) - timedelta(hours=1)}
    turns = []
    given = []

    async def is_on(redis):
        return state["on"]

    async def set_on(redis, on, user_id):
        state["on"] = on
        turns.append((on, user_id))

    async def two():
        return 2

    async def take_start(redis):
        started, state["started"] = state["started"], None

        return started

    async def put_back_start(redis, started):
        state["started"] = started

    async def give_time_back(stopped):
        given.append(stopped)

    monkeypatch.setattr(maintenance_routes, "is_on", is_on)
    monkeypatch.setattr(maintenance_routes, "set_on", set_on)
    monkeypatch.setattr(maintenance_routes, "take_start", take_start)
    monkeypatch.setattr(maintenance_routes, "put_back_start", put_back_start)
    monkeypatch.setattr(maintenance_routes.rounds, "running_interviews", two)
    monkeypatch.setattr(maintenance_routes.rounds, "give_time_back", give_time_back)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    yield turns, given, state
    app.dependency_overrides.clear()


def signed_in(user):
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[optional_user] = lambda: user


def test_anyone_reads_the_switch_and_learns_if_the_site_stays_open_to_them(client):
    assert client.get("/maintenance").json() == {"on": True, "superadmin": False}

    signed_in(BOB)

    assert client.get("/maintenance").json() == {"on": True, "superadmin": False}

    signed_in(ANN)

    assert client.get("/maintenance").json() == {"on": True, "superadmin": True}


def test_only_a_superadmin_reads_the_running_count_and_turns_it(client, switch):
    turns, _, _ = switch
    signed_in(BOB)

    assert client.get("/superadmin/maintenance").status_code == 404
    assert client.put("/superadmin/maintenance", json={"on": False}).status_code == 404

    signed_in(ANN)

    assert client.get("/superadmin/maintenance").json() == {"on": True, "running": 2}
    assert client.put("/superadmin/maintenance", json={"on": False}).json() == {
        "on": False,
        "running": 2,
    }
    assert turns == [(False, "ann")]


def test_the_switch_works_while_rounds_is_down(client, monkeypatch):
    async def down():
        raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(maintenance_routes.rounds, "running_interviews", down)
    signed_in(ANN)

    assert client.get("/superadmin/maintenance").json() == {"on": True, "running": None}


def test_turning_it_off_gives_running_interviews_the_time_it_was_on_once(client, switch):
    _, given, _ = switch
    signed_in(ANN)

    client.put("/superadmin/maintenance", json={"on": False})
    client.put("/superadmin/maintenance", json={"on": False})

    assert len(given) == 1
    assert timedelta(minutes=59) < given[0] < timedelta(minutes=61)


def test_if_rounds_cannot_give_the_time_back_it_stays_on_for_another_try(
    client, switch, monkeypatch
):
    turns, _, state = switch

    async def down(stopped):
        raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(maintenance_routes.rounds, "give_time_back", down)
    signed_in(ANN)

    assert client.put("/superadmin/maintenance", json={"on": False}).status_code == 502
    assert turns == []
    assert state["on"] and state["started"] is not None
