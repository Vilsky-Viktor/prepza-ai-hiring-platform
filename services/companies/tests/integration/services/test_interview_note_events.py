"""Each note change notifications hears about, against the real database: writing and editing a
note save its event with the change (its interview's title, the author as the team sees them, its
text), deleting one saves its deletion, and pinning saves none. An API key's note names the key."""

import uuid

import httpx
import pytest
from prepza_common.auth.key_actor import key_actor
from prepza_common.auth.service_auth import issue_token
from prepza_common.events.notes import NOTE_CREATED, NOTE_DELETED, NOTE_EDITED
from prepza_common.http.http import bearer
from sqlalchemy import select

from companies.config import settings
from companies.core.db import Session
from companies.integrations import accounts, api_keys
from companies.main import app
from companies.models.outbox import OutboxEvent
from companies.services import interview_notes
from tests.integration import factories
from tests.integration.factories import as_member


@pytest.fixture(autouse=True)
def names(monkeypatch):
    """Accounts knows the owner's name; the others go by email."""
    known = {}

    async def profiles(user_ids):
        return {uid: known[uid] for uid in user_ids if uid in known}

    monkeypatch.setattr(accounts, "profiles", profiles)

    return known


async def events(company_id) -> list[tuple[str, dict]]:
    """The company's note events, oldest first."""
    async with Session() as session:
        rows = await session.execute(
            select(OutboxEvent.event_type, OutboxEvent.data)
            .where(
                OutboxEvent.event_type.in_([NOTE_CREATED, NOTE_EDITED, NOTE_DELETED]),
                OutboxEvent.data["company_id"].astext == str(company_id),
            )
            .order_by(OutboxEvent.created_at)
        )

    return [tuple(row) for row in rows]


def test_writing_editing_and_deleting_a_note_each_save_an_event(run, names):
    async def scenario():
        team = await factories.team("note-events")
        names[team.owner] = {"name": "Olga Owner"}
        interview, company, owner = await as_member(team.owner, team.interview.id)
        note = await interview_notes.add(interview, company, owner, "Shortlist the top 5")
        await interview_notes.edit(interview, company, owner, note.id, "Shortlist the top 3")
        await interview_notes.pin(interview, company, owner, note.id, True)
        _, _, viewer = await as_member(team.viewer, team.interview.id)
        await interview_notes.add(interview, company, viewer, "Agreed")
        await interview_notes.delete(interview, company, owner, note.id)

        return team, note, await events(team.company.id)

    team, note, saved = run(scenario())

    assert [kind for kind, _ in saved] == [NOTE_CREATED, NOTE_EDITED, NOTE_CREATED, NOTE_DELETED]
    created, edited, by_viewer, deleted = (data for _, data in saved)
    assert {key: created[key] for key in ("note_id", "interview_id", "title", "text")} == {
        "note_id": str(note.id),
        "interview_id": str(team.interview.id),
        "title": team.interview.title,
        "text": "Shortlist the top 5",
    }
    assert (created["author_id"], created["author_name"], created["edited_at"]) == (
        team.owner,
        "Olga Owner",
        None,
    )
    assert (edited["text"], edited["created_at"]) == ("Shortlist the top 3", created["created_at"])
    assert edited["edited_at"] is not None
    # Without a name, the author goes by their email.
    assert (by_viewer["author_id"], by_viewer["author_name"]) == (
        team.viewer,
        f"{team.viewer}@example.com",
    )
    assert deleted == {
        "note_id": str(note.id),
        "company_id": str(team.company.id),
        "interview_id": str(team.interview.id),
    }


def test_an_api_keys_note_names_the_key(run, monkeypatch):
    key = uuid.uuid4()

    async def key_names(company_id, key_ids):
        return {str(key): "Zapier"} if str(key) in map(str, key_ids) else {}

    monkeypatch.setattr(api_keys, "names", key_names)

    async def scenario():
        team = await factories.team("note-key")
        token = bearer(issue_token("api", "companies", settings.service_secret))
        url = f"/internal/companies/{team.company.id}/interviews/{team.interview.id}/notes"
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://companies") as client:
            await client.post(
                url, params={"user_id": key_actor(key)}, headers=token, json={"text": "From CI"}
            )

        return await events(team.company.id)

    [(kind, data)] = run(scenario())

    assert (kind, data["author_id"], data["author_name"], data["text"]) == (
        NOTE_CREATED,
        key_actor(key),
        "Zapier",
        "From CI",
    )
