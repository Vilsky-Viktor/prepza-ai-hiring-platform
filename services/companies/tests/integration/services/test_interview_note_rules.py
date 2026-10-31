"""What guards an interview's notes, against the real database and Redis: a suspended company's
notes are read, not changed (409 with its code); a member's hourly notes (429); each change's
line in the action log, never the note's text; and the api service's routes, as the key itself."""

import uuid

import httpx
import pytest
from redis.asyncio import Redis
from sqlalchemy import select
from testee_common.auth.key_actor import key_actor
from testee_common.auth.service_auth import issue_token
from testee_common.events.audit_actions import AuditAction, TargetKind
from testee_common.http.http import bearer
from testee_common.limits import limits

from companies.config import settings
from companies.constants import error_codes
from companies.constants.invites import COMPANY_SUSPENDED
from companies.core.db import Session
from companies.integrations import accounts, api_keys
from companies.main import app
from companies.models.audit import AuditEvent
from companies.repositories import superadmin_companies
from companies.services import interview_notes
from tests.integration import factories
from tests.integration.factories import as_member
from tests.integration.transactions import transaction

TOO_MANY_REQUESTS = "Too many requests. Try again later."


@pytest.fixture(autouse=True)
def calls_elsewhere(monkeypatch):
    """Accounts knows no names (authors go by email); limit hits are recorded, not published."""
    hits = []

    async def profiles(user_ids):
        return {}

    async def recorded(event_type, data, attempts, timeout):
        hits.append(data)

    monkeypatch.setattr(accounts, "profiles", profiles)
    monkeypatch.setattr(limits, "publish_retried", recorded)

    return hits


async def refusal(call):
    with pytest.raises(Exception) as refused:
        await call

    return refused.value


def test_a_suspended_companys_notes_are_read_not_changed(run):
    async def scenario():
        team = await factories.team("suspended")
        interview, company, owner = await as_member(team.owner, team.interview.id)
        note = await interview_notes.add(interview, company, owner, "Before")
        await transaction(superadmin_companies.set_suspended, team.company.id, True)
        interview, company, owner = await as_member(team.owner, team.interview.id)
        refused = [
            await refusal(interview_notes.add(interview, company, owner, "After")),
            await refusal(interview_notes.edit(interview, company, owner, note.id, "After")),
            await refusal(interview_notes.pin(interview, company, owner, note.id, True)),
            await refusal(interview_notes.delete(interview, company, owner, note.id)),
        ]

        return refused, await interview_notes.page(interview, owner, 0, 20)

    refused, notes = run(scenario())

    assert [(item.status_code, item.detail, item.code) for item in refused] == [
        (409, COMPANY_SUSPENDED, error_codes.COMPANY_SUSPENDED)
    ] * 4
    assert [(note.text, note.pinned) for note in notes] == [("Before", False)]


def test_a_member_writes_at_most_their_hourly_notes(run, calls_elsewhere):
    async def scenario():
        team = await factories.team("limit")
        interview, company, viewer = await as_member(team.viewer, team.interview.id)
        redis = Redis.from_url(settings.redis_url)

        try:
            # The hour's 60 notes (the limit's default) already written.
            await redis.set(f"rate:notes:{team.viewer}", 60, ex=3600)
            refused = await refusal(interview_notes.add(interview, company, viewer, "One more"))
        finally:
            await redis.aclose()

        # Another member's notes are counted apart.
        _, _, owner = await as_member(team.owner, team.interview.id)
        await interview_notes.add(interview, company, owner, "Still mine")

        return team, refused, await interview_notes.page(interview, owner, 0, 20)

    team, refused, notes = run(scenario())

    assert (refused.status_code, refused.detail) == (429, TOO_MANY_REQUESTS)
    assert 0 < int(refused.headers["Retry-After"]) <= 3600
    assert [note.text for note in notes] == ["Still mine"]
    assert [(hit["limit"], hit["user_id"]) for hit in calls_elsewhere] == [
        ("NOTES_PER_USER_HOUR", team.viewer)
    ]


def test_each_change_is_logged_without_the_notes_text(run):
    async def scenario():
        team = await factories.team("logged")
        interview, company, admin = await as_member(team.admin, team.interview.id)
        note = await interview_notes.add(interview, company, admin, "Secret opinion")
        await interview_notes.edit(interview, company, admin, note.id, "Secret opinion, edited")
        await interview_notes.pin(interview, company, admin, note.id, True)
        # Pinning a pinned note changes nothing, so it logs nothing.
        await interview_notes.pin(interview, company, admin, note.id, True)
        await interview_notes.pin(interview, company, admin, note.id, False)
        await interview_notes.delete(interview, company, admin, note.id)

        async with Session() as session:
            rows = (
                await session.scalars(
                    select(AuditEvent)
                    .where(AuditEvent.company_id == team.company.id)
                    .order_by(AuditEvent.created_at)
                )
            ).all()

        return team, [row for row in rows if row.action.startswith("note_")]

    team, rows = run(scenario())

    assert [row.action for row in rows] == [
        AuditAction.NOTE_ADDED,
        AuditAction.NOTE_EDITED,
        AuditAction.NOTE_PINNED,
        AuditAction.NOTE_UNPINNED,
        AuditAction.NOTE_DELETED,
    ]
    assert {(row.user_id, row.target_kind, row.target_id) for row in rows} == {
        (team.admin, TargetKind.INTERVIEW, team.interview.id)
    }
    assert not [row for row in rows if "Secret" in str(row.target_label or "")]


async def api_call(method: str, team, user_id: str, **kwargs) -> httpx.Response:
    """The api service's call as `user_id`, the key acting (key_actor)."""
    token = bearer(issue_token("api", "companies", settings.service_secret))
    url = f"/internal/companies/{team.company.id}/interviews/{team.interview.id}/notes"
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://companies") as client:
        return await client.request(
            method, url, params={"user_id": user_id}, headers=token, **kwargs
        )


def test_the_api_reads_and_writes_notes_as_the_key_itself(run, monkeypatch):
    """No member: the note is the key's, named as it is now; another key may delete and pin it
    (an admin's), not edit it; someone who's no member gets nothing."""
    writer, reader = uuid.uuid4(), uuid.uuid4()

    async def names(company_id, key_ids):
        return {str(writer): "Zapier"}

    monkeypatch.setattr(api_keys, "names", names)

    async def scenario():
        team = await factories.team("api")
        body = {"text": "  Through the API  "}
        added = await api_call("POST", team, key_actor(writer), json=body)
        listed = await api_call("GET", team, key_actor(reader))
        stranger = await api_call("POST", team, f"gone-{uuid.uuid4()}", json={"text": "No"})

        async with Session() as session:
            logged = (
                await session.execute(
                    select(AuditEvent.user_id, AuditEvent.key_id, AuditEvent.via).where(
                        AuditEvent.company_id == team.company.id,
                        AuditEvent.action == AuditAction.NOTE_ADDED,
                    )
                )
            ).all()

        return added, listed, stranger, logged

    added, listed, stranger, logged = run(scenario())

    assert added.status_code == 201
    assert (added.json()["text"], added.json()["can_edit"]) == ("Through the API", True)
    assert added.json()["author"] == {
        "name": "Zapier",
        "photo_url": None,
        "former": False,
        "api_key": True,
    }
    assert [
        (item["text"], item["can_edit"], item["can_delete"], item["can_pin"])
        for item in listed.json()
    ] == [("Through the API", False, True, True)]
    assert stranger.status_code == 404
    assert [tuple(row) for row in logged] == [(key_actor(writer), writer, "api")]
