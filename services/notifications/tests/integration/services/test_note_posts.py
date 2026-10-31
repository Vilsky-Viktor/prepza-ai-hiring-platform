"""The team's notes in Slack and the activity digest, against the real database: each note is
posted once (a retry after Slack was busy posts it then), the digest keeps each note's newest
start whatever order its events come in, leaves out a deleted note and finds the companies with
notes, and old notes go each morning."""

import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from event_pushes import push
from testee_common.auth.encryption import encrypt

from notifications.config import settings
from notifications.constants.notes import PENDING_NOTE_HOURS
from notifications.core.db import Session
from notifications.integrations import companies
from notifications.integrations import slack as slack_api
from notifications.repositories import digest_activity, pending_notes
from notifications.repositories import slack as storage
from notifications.services import retention
from tests.integration.factories import api, company
from tests.integration.note_events import created, deleted, edited, note
from tests.integration.transactions import transaction

KEY = "Zm9vYmFyYmF6cXV4cXV1eGNvcmdlZ3JhdWx0Z2FycGw="


@pytest.fixture
def slack(monkeypatch):
    """Slack set up on the server; what's posted, or Slack busy (`busy`) for now."""
    found = {"posted": [], "busy": False}

    async def post(webhook, message):
        if found["busy"]:
            raise slack_api.SlackBusy("429")

        found["posted"].append(
            (webhook, [block.get("text", {}).get("text") for block in message["blocks"]])
        )

    async def editor(company_id, user_id):
        return {"member": True, "editor": True}

    monkeypatch.setattr(settings, "slack_client_id", "client")
    monkeypatch.setattr(settings, "slack_client_secret", "secret")
    monkeypatch.setattr(settings, "slack_encryption_key", KEY)
    monkeypatch.setattr(slack_api, "post", post)
    monkeypatch.setattr(companies, "access", editor)

    return found


async def deliver(*events: tuple) -> list[int]:
    async with api() as client:
        return [
            (await client.post("/internal/events", json=push(*event))).status_code
            for event in events
        ]


async def pending(company_id: str, hours: int = 1) -> list[tuple]:
    """The company's notes waiting for the digest, written in the last `hours`."""
    since = datetime.now(UTC) - timedelta(hours=hours)

    async with Session() as session:
        rows = await pending_notes.of_companies(
            session, [company_id], since, datetime.now(UTC) + timedelta(hours=1)
        )

    return [(row.excerpt, row.author_name) for row in rows]


def test_each_note_is_posted_once_with_its_text_and_retried_while_slack_is_busy(run, teams, slack):
    company_id, interview_id = company(), str(uuid.uuid4())
    teams[company_id] = ["ann", "bob"]
    first = note(company_id, interview_id, "ann", "<!channel> see www.evil.com", author_name="Ann")
    second = note(company_id, interview_id, "bob", "Agreed", author_name="Bob")

    async def scenario():
        await transaction(
            storage.connect,
            company_id,
            "Acme",
            "#hiring",
            encrypt(KEY, "https://hooks/hiring"),
            encrypt(KEY, "token"),
            "hash",
            ["note_added"],
            "ann",
        )
        event = created(first, "first")
        codes = await deliver(event, event)
        slack["busy"] = True
        codes += await deliver(created(second, "second"))
        slack["busy"] = False
        codes += await deliver(created(second, "second"))

        return codes

    codes = run(scenario())

    assert codes == [204, 204, 500, 204]
    assert [texts[:2] for _, texts in slack["posted"]] == [
        ["Ann added a note on “AI Engineer”:", "&lt;!channel&gt; see www.\u200bevil.\u200bcom"],
        ["Bob added a note on “AI Engineer”:", "Agreed"],
    ]


def test_a_company_without_notes_on_its_channel_gets_none(run, teams, slack):
    company_id = company()
    teams[company_id] = ["ann", "bob"]

    async def scenario():
        await transaction(
            storage.connect,
            company_id,
            "Acme",
            "#hiring",
            encrypt(KEY, "https://hooks/hiring"),
            encrypt(KEY, "token"),
            "hash",
            ["candidate_finished"],
            "ann",
        )
        await deliver(created(note(company_id, str(uuid.uuid4()), "ann", "Quiet")))

    run(scenario())

    assert slack["posted"] == []


def test_the_digest_keeps_each_notes_newest_start_and_drops_a_deleted_one(run, teams):
    company_id, interview_id = company(), str(uuid.uuid4())
    teams[company_id] = ["ann", "bob"]
    kept = note(company_id, interview_id, "ann", "First take", author_name="Ann")
    gone = note(company_id, interview_id, "bob", "Never mind", author_name="Bob")
    now = datetime.now(UTC)

    async def scenario():
        # The newer edit comes before the note itself and before an older edit: it stays.
        await deliver(
            edited(kept, "Third take", now + timedelta(minutes=2)),
            created(kept),
            edited(kept, "Second take", now + timedelta(minutes=1)),
            created(gone),
            deleted(gone),
        )

        return await pending(company_id)

    assert run(scenario()) == [("Third take", "Ann")]


def test_the_digest_finds_companies_with_notes_and_old_notes_go(run, teams):
    fresh, stale = company(), company()
    now = datetime.now(UTC)
    old = (now - timedelta(hours=PENDING_NOTE_HOURS - 1)).isoformat()

    async def scenario():
        await deliver(
            created(note(fresh, str(uuid.uuid4()), "ann", "New")),
            created(note(stale, str(uuid.uuid4()), "ann", "Old", created_at=old)),
        )

        async with Session() as session:
            found = await digest_activity.active_companies(
                session, [], now - timedelta(days=3), now + timedelta(hours=1), "", 1000
            )

        await retention.forget_old(now + timedelta(hours=2), time.monotonic() + 30)

        return found, await pending(fresh), await pending(stale, hours=72)

    found, left_fresh, left_stale = run(scenario())

    assert {fresh, stale} <= set(found)
    assert (left_fresh, left_stale) == ([("New", "Ann")], [])
