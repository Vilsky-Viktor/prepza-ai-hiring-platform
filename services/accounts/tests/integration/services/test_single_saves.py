"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the caller's retry finds the whole action still to do."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from prepza_common.auth.user import User
from prepza_common.events.deletions import USER_DELETED
from sqlalchemy import select

from accounts.core.db import Session
from accounts.integrations import services
from accounts.models.outbox import OutboxEvent
from accounts.repositories import erasures, legal
from accounts.services import deletion
from accounts.services import outbox as outbox_service
from tests.integration.transactions import transaction


async def broken(*args):
    raise RuntimeError("The database went away")


@pytest.fixture
def leaving(monkeypatch):
    """A user deleting their account, with companies' part done and the sign-in's deletion and
    the event's publishing recorded rather than made."""
    user = User(uid=f"leaving-{uuid.uuid4()}", email="leaving@example.com", email_verified=True)
    signed_out = []

    async def deleted(user_id, email):
        pass

    async def unpublished():
        pass

    monkeypatch.setattr(services, "delete_in_companies", deleted)
    monkeypatch.setattr(outbox_service, "flush_quietly", unpublished)
    monkeypatch.setattr(deletion, "delete_sign_in", signed_out.append)

    return user, signed_out


async def events_about(user_id: str) -> list[dict]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent).where(OutboxEvent.data["user_id"].astext == user_id)
        )

        return [{"type": row.event_type, **row.data} for row in rows]


def test_an_account_deletion_saves_its_rows_note_and_event_together(run, leaving):
    """Accounts' rows go with the note that replays the deletion after a restore and the
    `user.deleted` event every other holder deletes its part by; then the sign-in goes."""
    user, signed_out = leaving

    async def scenario():
        await transaction(legal.accept_terms, user.uid, "2026-10-10")
        await deletion.delete_account(user)
        noted = await transaction(erasures.page, datetime.now(UTC) - timedelta(hours=1), None, 1000)

        return (
            await transaction(legal.accepted_terms, user.uid),
            [item.email for item in noted if item.user_id == user.uid],
            await events_about(user.uid),
        )

    terms, noted, events = run(scenario())

    assert terms == []
    assert noted == ["leaving@example.com"]
    assert events == [{"type": USER_DELETED, "user_id": user.uid, "email": "leaving@example.com"}]
    assert signed_out == [user.uid]


def test_an_account_deletion_whose_erasure_note_fails_keeps_the_accounts_rows(
    run, leaving, monkeypatch
):
    """A failed note leaves the rows and the sign-in for the user's retry, and tells no holder:
    never rows deleted that a restore would bring back unnoticed."""
    user, signed_out = leaving
    monkeypatch.setattr(erasures, "record", broken)

    async def scenario():
        await transaction(legal.accept_terms, user.uid, "2026-10-10")

        with pytest.raises(RuntimeError):
            await deletion.delete_account(user)

        return await transaction(legal.accepted_terms, user.uid), await events_about(user.uid)

    terms, events = run(scenario())

    assert [row["version"] for row in terms] == ["2026-10-10"]
    assert events == []
    assert signed_out == []
