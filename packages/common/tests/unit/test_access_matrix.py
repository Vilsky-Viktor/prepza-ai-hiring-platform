"""The access matrix (tests/access_matrix.py) on a small app of its own: it finds the routes
taking ids, asks for a reason for those it leaves out, and catches a route that checks the
company but not the object, and one that lets a viewer change things."""

import asyncio
from uuid import UUID

import access_matrix
import pytest
from access_matrix import ALLOWED, REFUSED, SIGNED_OUT, Side, World
from fastapi import FastAPI, HTTPException
from prepza_common.auth.auth import CurrentUser
from prepza_common.auth.superadmin import SuperadminUser
from pydantic import BaseModel

OWNED = {"company_id", "note_id"}
ROLES = {("a", "ann"): "owner", ("a", "vic"): "viewer", ("b", "bob"): "owner"}
NOTES = {"n-a": "a", "n-b": "b"}


class NoteIn(BaseModel):
    text: str


def require(company_id: str, user_id: str, editor: bool = False) -> None:
    role = ROLES.get((company_id, user_id))

    if role is None:
        raise HTTPException(404)

    if editor and role != "owner":
        raise HTTPException(403)


app = FastAPI()


@app.get("/notes/{note_id}")
async def read_note(note_id: str, company_id: str, user: CurrentUser) -> dict:
    require(company_id, user.uid)

    if NOTES.get(note_id) != company_id:
        raise HTTPException(404)

    return {}


@app.put("/notes/{note_id}")
async def change_note(note_id: str, company_id: str, body: NoteIn, user: CurrentUser) -> dict:
    """Checks the company, not that the note is the company's."""
    require(company_id, user.uid, editor=True)

    return {}


@app.delete("/notes/{note_id}")
async def remove_note(note_id: str, company_id: str, user: CurrentUser) -> dict:
    """Lets a viewer remove it."""
    require(company_id, user.uid)

    if NOTES.get(note_id) != company_id:
        raise HTTPException(404)

    return {}


@app.get("/superadmin/companies/{company_id}")
async def look_up(company_id: str, superadmin: SuperadminUser) -> dict:
    return {}


@app.get("/pages/{key}")
async def page(key: str) -> dict:
    return {}


@app.get("/internal/notes/{note_id}")
async def internal(note_id: UUID) -> dict:
    return {}


@pytest.fixture
def world(monkeypatch):
    mine = Side("ann", {"company_id": "a", "note_id": "n-a"}, "vic")
    theirs = Side("bob", {"company_id": "b", "note_id": "n-b"})

    return access_matrix.enter(monkeypatch, World(mine, theirs))


def found(route: str, world) -> dict:
    by_name = {str(item): item for item in access_matrix.routes(app, OWNED, {})}

    return asyncio.run(access_matrix.outcomes(app, by_name[route], world, {}, {}))[0]


def test_it_calls_every_user_route_taking_an_owned_id_and_asks_why_for_the_rest():
    names = [str(route) for route in access_matrix.routes(app, OWNED, {})]

    assert names == [
        "GET /notes/{note_id}",
        "PUT /notes/{note_id}",
        "DELETE /notes/{note_id}",
        "GET /superadmin/companies/{company_id}",
    ]
    assert access_matrix.unlisted(app, OWNED, {}) == ["GET /pages/{key}"]
    assert access_matrix.unlisted(app, OWNED, {"GET /pages/{key}": "Public.", "GET /x": "?"}) == [
        "gone: GET /x"
    ]


def test_a_route_checking_its_objects_matches_what_is_expected(world):
    route = "GET /notes/{note_id}"
    expected = access_matrix.expected(access_matrix.routes(app, OWNED, {})[0], world, {})

    assert found(route, world) == expected
    assert expected == {
        "owner": ALLOWED,
        "outsider": REFUSED,
        "signed out": SIGNED_OUT,
        "cross note_id": REFUSED,
        "cross company_id": REFUSED,
        "viewer": ALLOWED,
    }


def test_another_companys_object_and_a_viewers_change_are_caught(world):
    assert found("PUT /notes/{note_id}", world)["cross note_id"] == ALLOWED
    assert found("DELETE /notes/{note_id}", world)["viewer"] == ALLOWED


def test_a_superadmin_route_lets_only_the_superadmin_through(world):
    assert found("GET /superadmin/companies/{company_id}", world) == {
        "signed out": REFUSED,
        "user": REFUSED,
        "superadmin": ALLOWED,
    }
