import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from babel.dates import format_date
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.notifications import EVERYONE, Recipient

from notifications.constants.legal_notices import ALREADY_ASKED
from notifications.main import app
from notifications.repositories import bulk_sends, notifications
from notifications.services import bulk, delivery, legal_notices
from tests.integration.factories import api
from tests.integration.transactions import transaction

# Far enough ahead to be noticed, and a version of its own in the shared database.
LATER = (datetime.now(UTC).date() + timedelta(days=30 + uuid.uuid4().int % 300)).isoformat()


async def large_resend_quota(redis):
    return {"RESEND_DAILY_LIMIT": 1_000_000}


@pytest.fixture
def terms(monkeypatch):
    """New terms from LATER; every account is two users and a guest candidate; delivery is
    recorded by its key."""
    ann, bob = f"u-{uuid.uuid4()}", f"u-{uuid.uuid4()}"
    sent = []

    async def user_ids(after, setting=None):
        return [ann, bob, "guest-1"]

    async def recipients(ids):
        return [
            {"user_id": one, "email": f"{one}@example.com", "language": "en", "preferences": {}}
            for one in ids
        ]

    async def transmit(email, key):
        sent.append((email.to, email.subject, key))

    async def no_wait(_seconds):
        return None

    monkeypatch.setitem(legal_notices.LEGAL_VERSIONS, "terms", LATER)
    monkeypatch.setattr("notifications.services.audiences.library.user_ids", user_ids)
    monkeypatch.setattr(bulk.library, "recipients", recipients)
    monkeypatch.setattr(delivery, "transmit", transmit)
    monkeypatch.setattr("notifications.services.bulk.asyncio.sleep", no_wait)
    monkeypatch.setattr("prepza_common.limits.limits.current_values", large_resend_quota)

    return ann, bob, sent


def as_user(uid: str) -> None:
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


def test_a_notice_is_asked_once_goes_in_everyones_bell_and_emails_each_account_once(run, terms):
    ann, bob, sent = terms

    async def ask():
        try:
            await legal_notices.ask("terms", "sam")
        except HTTPException as refused:
            return refused.detail

        return None

    async def scenario():
        asked = await asyncio.gather(ask(), ask())
        send = await transaction(bulk_sends.get, "legal_terms", LATER)
        everyone = [
            item
            for item in await transaction(
                notifications.latest,
                [(Recipient.USER, ann)],
                100,
                datetime.now(UTC) - timedelta(days=1),
            )
            if item.kind == "legal_terms" and item.data.get("date") == LATER
        ]
        await bulk.send_bulk(datetime.now(UTC))
        await bulk.send_bulk(datetime.now(UTC))
        states = {item["document"]: item["state"] for item in await legal_notices.states()}

        as_user(bob)

        async with api() as client:
            banner = (await client.get("/me/legal-changes")).json()

        app.dependency_overrides.clear()

        return asked, send, everyone, states, banner

    asked, send, everyone, states, banner = run(scenario())
    mine = sorted(item for item in sent if item[2].startswith(f"bulk/{send.id}/"))

    assert sorted(asked, key=str) == [None, ALREADY_ASKED]
    assert [(item.recipient, item.recipient_id, item.link) for item in everyone] == [
        (Recipient.ALL, EVERYONE, "/terms")
    ]
    # Never the guest candidate, and once each however many runs.
    assert [(to, key) for to, _, key in mine] == sorted(
        [(f"{user}@example.com", f"bulk/{send.id}/{user}") for user in (ann, bob)]
    )
    # The day it applies, as English writes it.
    day = format_date(date.fromisoformat(LATER), "long", locale="en")
    assert all(day in subject for _, subject, _ in mine)
    assert states["terms"] == "sent"
    assert {"document": "terms", "version": LATER} in banner
