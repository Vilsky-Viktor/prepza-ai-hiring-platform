"""The routes taking a user's id are the superadmin's: everyone else, the user included, is
refused (access_matrix, .claude/rules/testing.md, Security)."""

from types import SimpleNamespace

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id
from firebase_admin import auth as firebase_auth

from accounts.main import app

OWNED = {"user_id"}

NOT_OWNED = {}

BODIES = {"PUT /superadmin/emails/{user_id}/preferences": {"changes": {"updates": False}}}


def side(kind: str) -> Side:
    user = user_id(kind)

    return Side(user, {"user_id": user})


@pytest.fixture
def world(monkeypatch):
    """Firebase knows every account by its id."""
    monkeypatch.setattr(
        firebase_auth,
        "get_user",
        lambda uid: SimpleNamespace(uid=uid, email=f"{uid}@example.com"),
    )

    return access_matrix.enter(monkeypatch, World(side("mine"), side("theirs")))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


def test_no_internal_route_takes_an_id_with_another_that_scopes_it():
    """None today: one that comes is scoped in the internal matrix (internal_matrix)."""
    assert internal_matrix.unlisted(app, OWNED, {}, {}) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, {}))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
