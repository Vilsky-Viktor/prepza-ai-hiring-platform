"""How a note's author shows: their name and picture from accounts, their email without a name or
while accounts can't be reached, a former member once their membership is gone, and an API key by
its name now (none once deleted)."""

import asyncio
import json
import uuid

import httpx
from prepza_common.auth.key_actor import key_actor
from prepza_common.http import http

from companies.integrations import accounts
from companies.models.companies import Member
from companies.models.interview_notes import InterviewNote
from companies.services import interview_notes

ANN = Member(user_id="ann", invited_email="ann@example.com", role="owner")
BOB = Member(user_id="bob", invited_email="bob@example.com", role="viewer")
# A member's note: written by a membership, not an API key.
BY_MEMBER = InterviewNote()


def accounts_answering(status: int, profiles: list[dict]):
    """Accounts' profiles route; returns the bodies it was sent."""
    sent = []

    def handler(request):
        sent.append((request.url.path, json.loads(request.content)))

        return httpx.Response(status, json={"profiles": profiles})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), sent


def test_authors_show_by_name_or_email_and_a_former_member_by_neither(monkeypatch):
    client, sent = accounts_answering(
        200, [{"user_id": "ann", "name": "Ann Lee", "photo_url": "https://example.com/ann.png"}]
    )
    monkeypatch.setattr(http, "get_client", lambda: client)

    # Bob twice, as an author of two notes: asked for once.
    profiles = asyncio.run(interview_notes.profiles_of([BOB, ANN, BOB]))
    authors = [
        interview_notes.author_of(BY_MEMBER, item, profiles, {}) for item in (ANN, BOB, None)
    ]

    assert sent == [("/internal/accounts/profiles", {"user_ids": ["ann", "bob"]})]
    assert [(item.name, item.photo_url, item.former) for item in authors] == [
        ("Ann Lee", "https://example.com/ann.png", False),
        ("bob@example.com", None, False),
        (None, None, True),
    ]


def test_authors_show_by_email_while_accounts_is_down(monkeypatch):
    client, _ = accounts_answering(503, [])
    monkeypatch.setattr(http, "get_client", lambda: client)

    profiles = asyncio.run(interview_notes.profiles_of([ANN]))

    assert profiles == {}
    assert interview_notes.author_of(BY_MEMBER, ANN, profiles, {}).name == "ann@example.com"


def test_no_authors_ask_accounts_nothing(monkeypatch):
    client, sent = accounts_answering(200, [])
    monkeypatch.setattr(http, "get_client", lambda: client)

    assert asyncio.run(accounts.profiles([])) == {}
    assert sent == []


def test_an_api_keys_note_is_by_the_key_named_as_it_is_now_and_only_it_edits_it(monkeypatch):
    kept, deleted = uuid.uuid4(), uuid.uuid4()
    names = {str(kept): "Zapier v2"}
    by_key = InterviewNote(author_key_id=kept)
    by_deleted = InterviewNote(author_key_id=deleted)
    key = Member(user_id=key_actor(kept), invited_email="", role="admin")
    other_key = Member(user_id=key_actor(deleted), invited_email="", role="admin")

    authors = [interview_notes.author_of(note, None, {}, names) for note in (by_key, by_deleted)]

    assert [(item.name, item.api_key, item.former) for item in authors] == [
        ("Zapier v2", True, False),
        (None, True, False),
    ]
    assert interview_notes.is_author(by_key, key)
    assert not interview_notes.is_author(by_key, other_key)
    # A key never counts as the author of a former member's note (no membership either side).
    assert not interview_notes.is_author(InterviewNote(), key)
    # Nor a member of a key's.
    assert not interview_notes.is_author(by_key, Member(user_id="ann", role="owner"))
