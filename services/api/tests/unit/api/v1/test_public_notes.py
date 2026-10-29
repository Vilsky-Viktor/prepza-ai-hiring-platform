"""An interview's notes through the public API: read and added as the key's creator, within the
key's company, a retried add answered with the first note."""

import uuid

import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException

from api.constants.permissions import Permission
from api.integrations import companies
from api.services import idempotency
from tests.unit.api.v1.test_list_links import next_page
from tests.unit.api_keys import call
from tests.unit.conftest import COMPANY, INTERVIEW

NOTES = f"/interviews/{INTERVIEW}/notes"


def note(text: str, name: str | None = "Maria Schmidt", pinned: bool = False) -> dict:
    """A note as companies' internal API returns it."""
    return {
        "id": str(uuid.uuid4()),
        "text": text,
        "author": {"name": name, "photo_url": None, "former": name is None},
        "pinned": pinned,
        "created_at": "2026-10-02T09:15:00Z",
        "edited_at": None,
        "can_edit": False,
        "can_delete": False,
        "can_pin": False,
    }


@pytest.fixture
def notes_api(monkeypatch, companies_api):
    """Companies' notes of COMPANY's interview, faked (with the rest of companies): the notes
    newest first, the pages asked for, and the status it refuses an add with."""
    state = {"notes": [], "asked": [], "added": [], "refuse": None}

    def ours(company_id, interview_id):
        if company_id != COMPANY or interview_id != INTERVIEW:
            raise HTTPException(404, "Interview not found")

    async def notes(company_id, interview_id, user_id, offset, limit):
        ours(company_id, interview_id)
        state["asked"].append((user_id, offset, limit))

        return state["notes"][offset : offset + limit]

    async def add_note(company_id, interview_id, text, user_id):
        ours(company_id, interview_id)

        if state["refuse"]:
            raise HTTPException(state["refuse"], "Refused")

        made = note(text)
        state["notes"].insert(0, made)
        state["added"].append((text, user_id))

        return made

    monkeypatch.setattr(companies, "notes", notes)
    monkeypatch.setattr(companies, "add_note", add_note)
    monkeypatch.setattr(idempotency, "get_redis", lambda: redis)
    redis = FakeRedis()

    return state


def test_a_key_reads_the_notes_as_its_creator_with_their_authors_names(client, key, notes_api):
    notes_api["notes"] = [note("Call Lena", pinned=True), note("Left us", name=None)]

    response = call(client, "GET", NOTES)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": notes_api["notes"][0]["id"],
            "text": "Call Lena",
            "author": "Maria Schmidt",
            "pinned": True,
            "created_at": "2026-10-02T09:15:00Z",
            "edited_at": None,
        },
        # A former member's note keeps its text, without their name.
        {
            "id": notes_api["notes"][1]["id"],
            "text": "Left us",
            "author": None,
            "pinned": False,
            "created_at": "2026-10-02T09:15:00Z",
            "edited_at": None,
        },
    ]
    assert notes_api["asked"] == [("u1", 0, 100)]


def test_a_full_page_of_notes_links_the_next_and_the_last_doesnt(client, key, notes_api):
    notes_api["notes"] = [note(f"Note {number}") for number in range(3)]

    full = call(client, "GET", NOTES, params={"offset": 1, "limit": 1})
    last = call(client, "GET", NOTES, params={"offset": 2, "limit": 5})

    assert [item["text"] for item in full.json()] == ["Note 1"]
    assert next_page(full) == (f"/api/v1{NOTES}", {"offset": "2", "limit": "1"})
    assert next_page(last) is None


def test_a_key_adds_a_note_as_its_creator(client, key, notes_api):
    response = call(client, "POST", NOTES, json={"text": "Shortlist five"})

    assert response.status_code == 201
    assert response.json()["text"] == "Shortlist five"
    assert response.json()["author"] == "Maria Schmidt"
    assert notes_api["added"] == [("Shortlist five", "u1")]


def test_a_retried_note_is_added_once_and_answered_with_the_first(client, key, notes_api):
    first = call(client, "POST", NOTES, json={"text": "Shortlist five"})
    again = call(client, "POST", NOTES, json={"text": "Shortlist five"})
    other = call(client, "POST", NOTES, json={"text": "Call Lena"})

    assert (first.status_code, again.status_code, other.status_code) == (201, 200, 201)
    assert again.json() == first.json()
    assert notes_api["added"] == [("Shortlist five", "u1"), ("Call Lena", "u1")]


def test_a_retry_after_the_first_note_was_deleted_finds_nothing(client, key, notes_api):
    call(client, "POST", NOTES, json={"text": "Shortlist five"})
    notes_api["notes"] = []

    again = call(client, "POST", NOTES, json={"text": "Shortlist five"})

    assert again.status_code == 404
    assert again.json()["detail"] == "Note not found"
    assert notes_api["added"] == [("Shortlist five", "u1")]


@pytest.mark.parametrize("text", ["", "x" * 2001])
def test_an_empty_or_too_long_note_is_refused(client, key, notes_api, text):
    response = call(client, "POST", NOTES, json={"text": text})

    assert response.status_code == 422
    assert notes_api["added"] == []


@pytest.mark.parametrize("refusal", [404, 409, 422, 429])
def test_companies_refusals_of_a_note_pass_through(client, key, notes_api, refusal):
    notes_api["refuse"] = refusal

    response = call(client, "POST", NOTES, json={"text": "Shortlist five"})

    assert response.status_code == refusal
    assert notes_api["added"] == []


def test_another_companys_interviews_notes_are_not_found(client, key, notes_api):
    other = f"/interviews/{uuid.uuid4()}/notes"

    assert call(client, "GET", other).status_code == 404
    assert call(client, "POST", other, json={"text": "Shortlist five"}).status_code == 404
    assert notes_api["added"] == []


@pytest.mark.parametrize(
    ("method", "body", "permission"),
    [("GET", None, Permission.NOTES_READ), ("POST", {"text": "Hi"}, Permission.NOTES_ADD)],
)
def test_a_key_without_the_notes_permission_is_refused(
    client, key, notes_api, method, body, permission
):
    key.permissions = [item for item in Permission if item != permission]

    response = call(client, method, NOTES, json=body)

    assert response.status_code == 403
    assert response.json()["code"] == "missing_permission"
    assert notes_api["asked"] == notes_api["added"] == []
