"""How a note's author shows: their name and picture from accounts, their email without a name or
while accounts can't be reached, and a former member once their membership is gone."""

import asyncio
import json

import httpx
from prepza_common.http import http

from companies.integrations import accounts
from companies.models.companies import Member
from companies.services import interview_notes

ANN = Member(user_id="ann", invited_email="ann@example.com", role="owner")
BOB = Member(user_id="bob", invited_email="bob@example.com", role="viewer")


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
    authors = [interview_notes.author_of(item, profiles) for item in (ANN, BOB, None)]

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
    assert interview_notes.author_of(ANN, profiles).name == "ann@example.com"


def test_no_authors_ask_accounts_nothing(monkeypatch):
    client, sent = accounts_answering(200, [])
    monkeypatch.setattr(http, "get_client", lambda: client)

    assert asyncio.run(accounts.profiles([])) == {}
    assert sent == []
