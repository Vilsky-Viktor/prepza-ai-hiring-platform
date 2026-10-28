"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the caller's retry finds the whole action still to do."""

import uuid

import pytest
from prepza_common.auth.user import User

from accounts.integrations import services
from accounts.repositories import erasures, legal
from accounts.services import deletion
from tests.integration.transactions import transaction


async def broken(*args):
    raise RuntimeError("The database went away")


def test_an_account_deletion_whose_erasure_note_fails_keeps_the_accounts_rows(run, monkeypatch):
    """Accounts' rows and the note that replays the deletion after a restore go together: a
    failed note leaves the rows and the sign-in for the user's retry, never rows deleted that a
    restore would bring back unnoticed."""
    user = User(uid=f"leaving-{uuid.uuid4()}", email="leaving@example.com", email_verified=True)
    signed_out = []

    async def deleted(service, user_id, email):
        pass

    monkeypatch.setattr(services, "delete_user", deleted)
    monkeypatch.setattr(deletion, "delete_sign_in", signed_out.append)
    monkeypatch.setattr(erasures, "record", broken)

    async def scenario():
        await transaction(legal.accept_terms, user.uid, "2026-10-10")

        with pytest.raises(RuntimeError):
            await deletion.delete_account(user)

        return await transaction(legal.accepted_terms, user.uid)

    assert [row["version"] for row in run(scenario())] == ["2026-10-10"]
    assert signed_out == []
