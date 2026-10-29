# The key and changes fixtures are imported from the route tests and named in the tests.
# ruff: noqa: F811
import importlib.util
import re
import uuid
from pathlib import Path

import pytest

from api.constants.permissions import Permission
from api.helpers.keys import with_implied
from api.integrations import companies
from tests.unit.api.v1.test_api_changes import changes  # noqa: F401 (fixture)
from tests.unit.api.v1.test_public_notes import notes_api  # noqa: F401 (fixture)
from tests.unit.api_keys import call
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW, sign_in

CANDIDATE_PATH = f"/interviews/{INTERVIEW}/candidates/{CANDIDATE}"
KEYS = f"/manage/keys?company_id={COMPANY}"
# Every public route, a request to it and the permission it needs.
ROUTES = [
    ("GET", "/interviews", None, Permission.INTERVIEWS_READ),
    ("GET", f"/interviews/{INTERVIEW}", None, Permission.INTERVIEWS_READ),
    ("POST", "/interviews", {"job_description": "Backend"}, Permission.INTERVIEWS_CREATE),
    ("GET", f"/interviews/{INTERVIEW}/candidates", None, Permission.CANDIDATES_READ),
    ("GET", CANDIDATE_PATH, None, Permission.CANDIDATES_READ),
    ("GET", "/candidates?email=bob@example.com", None, Permission.CANDIDATES_READ),
    ("POST", "/candidates/search", {"email": "bob@example.com"}, Permission.CANDIDATES_READ),
    (
        "POST",
        f"/interviews/{INTERVIEW}/candidates",
        {"email": "bob@example.com"},
        Permission.CANDIDATES_INVITE,
    ),
    ("POST", f"{CANDIDATE_PATH}/resend", None, Permission.CANDIDATES_INVITE),
    ("PATCH", CANDIDATE_PATH, {"name": "Anna"}, Permission.CANDIDATES_CHANGE),
    ("DELETE", CANDIDATE_PATH, None, Permission.CANDIDATES_DELETE),
    ("GET", f"/interviews/{INTERVIEW}/notes", None, Permission.NOTES_READ),
    ("POST", f"/interviews/{INTERVIEW}/notes", {"text": "Call Lena"}, Permission.NOTES_ADD),
    ("GET", "/credits", None, Permission.CREDITS_READ),
]


@pytest.fixture
def company_reads(monkeypatch):
    async def find(company_id, email):
        return []

    async def credits(company_id):
        return {"available": 1500, "reserved": 500, "candidates": 3, "low": False}

    monkeypatch.setattr(companies, "find_candidates", find)
    monkeypatch.setattr(companies, "credits", credits)


@pytest.mark.parametrize(("method", "path", "body", "permission"), ROUTES)
def test_a_route_refuses_a_key_without_its_permission(
    client, key, changes, company_reads, notes_api, method, path, body, permission
):
    key.permissions = [item for item in Permission if item != permission]

    response = call(client, method, path, json=body)

    assert response.status_code == 403
    assert response.json() == {
        "detail": f"This API key doesn't have the {permission} permission.",
        "code": "missing_permission",
    }
    assert changes == notes_api["added"] == []


@pytest.mark.parametrize(("method", "path", "body", "permission"), ROUTES)
def test_a_route_takes_a_key_with_only_its_permission(
    client, key, changes, company_reads, notes_api, method, path, body, permission
):
    key.permissions = with_implied([permission])

    assert call(client, method, path, json=body).status_code < 400


def test_every_public_route_declares_its_permission_and_the_docs_name_it(client):
    spec = client.get("/openapi.json").json()
    operations = [operation for path in spec["paths"].values() for operation in path.values()]
    named = [
        re.search(r"Needs the `(.+)` permission\.", operation["description"])
        for operation in operations
    ]

    assert len(operations) == len(ROUTES)
    assert all(named)
    assert sorted(found[1] for found in named) == sorted(route[3] for route in ROUTES)


def test_a_change_comes_with_reading_what_it_changes():
    assert with_implied([Permission.CANDIDATES_INVITE, Permission.INTERVIEWS_CREATE]) == [
        Permission.INTERVIEWS_READ,
        Permission.INTERVIEWS_CREATE,
        Permission.CANDIDATES_READ,
        Permission.CANDIDATES_INVITE,
    ]
    assert with_implied([Permission.NOTES_ADD]) == [Permission.NOTES_READ, Permission.NOTES_ADD]
    assert with_implied([Permission.CREDITS_READ, Permission.MCP]) == [
        Permission.CREDITS_READ,
        Permission.MCP,
    ]


def test_a_new_key_starts_with_the_two_reads(client, companies_api, stored):
    sign_in()
    made = client.post(KEYS, json={"name": "Site", "expiry": "1"}).json()
    page = client.get(f"/manage?company_id={COMPANY}").json()

    assert made["permissions"] == ["interviews:read", "candidates:read"]
    assert page["default_permissions"] == ["interviews:read", "candidates:read"]
    assert page["implied"]["candidates:invite"] == "candidates:read"
    assert page["implied"]["notes:add"] == "notes:read"
    assert page["permission_groups"]["notes"] == ["notes:read", "notes:add"]
    assert page["keys"][0]["permissions"] == ["interviews:read", "candidates:read"]


def test_a_new_key_gets_what_was_ticked_and_the_reads_it_implies(client, companies_api, stored):
    sign_in()
    body = {"name": "Site", "expiry": "1", "permissions": ["candidates:invite", "mcp"]}
    made = client.post(KEYS, json=body).json()

    assert made["permissions"] == ["candidates:read", "candidates:invite", "mcp"]
    assert stored["keys"][0].permissions == made["permissions"]


@pytest.mark.parametrize("permissions", [[], ["candidates:everything"]])
def test_a_key_needs_at_least_one_known_permission(client, companies_api, stored, permissions):
    sign_in()
    body = {"name": "Site", "expiry": "1", "permissions": permissions}

    assert client.post(KEYS, json=body).status_code == 422
    assert stored["keys"] == []


def made_key(client, permissions):
    sign_in()
    body = {"name": "Site", "expiry": "1", "permissions": permissions}

    return client.post(KEYS, json=body).json()["id"]


def change(client, key_id, permissions):
    path = f"/manage/keys/{key_id}?company_id={COMPANY}"

    return client.patch(path, json={"permissions": permissions})


def test_a_keys_permissions_are_taken_away_keeping_the_reads_they_imply(
    client, companies_api, stored
):
    key_id = made_key(client, ["candidates:invite", "candidates:delete", "credits:read"])

    response = change(client, key_id, ["candidates:invite"])

    assert response.status_code == 200
    assert response.json()["permissions"] == ["candidates:read", "candidates:invite"]
    assert stored["keys"][0].permissions == ["candidates:read", "candidates:invite"]
    # The action log gets what was taken away, and by whom.
    assert stored["changed"] == [
        (stored["keys"][0].id, "u1", ["candidates:delete", "credits:read"])
    ]


def test_a_key_gains_permissions_with_the_reads_they_imply(client, companies_api, stored):
    key_id = made_key(client, ["credits:read"])

    response = change(client, key_id, ["credits:read", "candidates:invite", "mcp"])

    assert response.status_code == 200
    assert response.json()["permissions"] == [
        "candidates:read",
        "candidates:invite",
        "credits:read",
        "mcp",
    ]
    assert stored["keys"][0].permissions == response.json()["permissions"]
    # Logged as a change that took nothing away.
    assert stored["changed"] == [(stored["keys"][0].id, "u1", None)]


def test_the_same_permissions_again_change_nothing(client, companies_api, stored):
    key_id = made_key(client, ["candidates:invite"])

    response = change(client, key_id, ["candidates:invite"])

    assert response.status_code == 200
    assert stored["keys"][0].permissions == ["candidates:read", "candidates:invite"]
    assert stored["changed"] == []


@pytest.mark.parametrize("permissions", [[], ["candidates:read", "candidates:everything"]])
def test_a_key_keeps_at_least_one_known_permission(client, companies_api, stored, permissions):
    key_id = made_key(client, ["candidates:read"])

    assert change(client, key_id, permissions).status_code == 422
    assert stored["keys"][0].permissions == ["candidates:read"]
    assert stored["changed"] == []


def test_only_editors_change_their_companys_keys(client, companies_api, stored):
    key_id = made_key(client, ["candidates:read", "credits:read"])
    companies_api["roles"]["u2"] = "viewer"
    sign_in("u2")

    assert change(client, key_id, ["mcp"]).status_code == 403
    assert change(client, "00000000-0000-0000-0000-000000000000", ["mcp"]).status_code == 403
    sign_in()
    assert change(client, "00000000-0000-0000-0000-000000000000", ["mcp"]).status_code == 404
    assert stored["keys"][0].permissions == ["candidates:read", "credits:read"]
    assert stored["changed"] == []


def test_another_companys_key_is_not_found(client, companies_api, stored):
    key_id = made_key(client, ["credits:read"])
    stored["keys"][0].company_id = uuid.uuid4()

    assert change(client, key_id, ["mcp"]).status_code == 404
    assert stored["keys"][0].permissions == ["credits:read"]
    assert stored["changed"] == []


def test_keys_made_before_permissions_keep_the_api_permissions_there_were_but_mcp():
    path = Path(__file__).resolve().parents[3] / "migrations/versions/0005_key_permissions.py"
    spec = importlib.util.spec_from_file_location("migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    # The notes permissions came later: a key gets them only when they're ticked.
    later = {Permission.MCP, Permission.NOTES_READ, Permission.NOTES_ADD}
    assert migration.EXISTING == [item for item in Permission if item not in later]
    assert migration.DEFAULT == ["interviews:read", "candidates:read"]
