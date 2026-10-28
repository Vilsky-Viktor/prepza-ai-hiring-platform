"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the caller's retry finds the whole action still to do."""

import uuid

import pytest
from prepza_common.auth.user import User

from library.integrations import accounts as account_services
from library.repositories import erasures, feedback
from library.services import accounts
from tests.integration.factories import interview, question_ids
from tests.integration.transactions import transaction


async def broken(*args):
    raise RuntimeError("The database went away")


def test_an_account_deletion_whose_erasure_note_fails_keeps_the_accounts_rows(run, monkeypatch):
    """Library's rows and the note that replays the deletion after a restore go together: a
    failed note leaves the rows and the sign-in for the user's retry, never rows deleted that a
    restore would bring back unnoticed."""
    user = User(uid=f"leaving-{uuid.uuid4()}", email="leaving@example.com", email_verified=True)
    signed_out = []

    async def deleted(service, user_id, email):
        pass

    monkeypatch.setattr(account_services, "delete_user", deleted)
    monkeypatch.setattr(accounts, "delete_sign_in", signed_out.append)
    monkeypatch.setattr(erasures, "record", broken)

    async def scenario():
        [question, *_] = await question_ids(await interview("Leaving"))
        await transaction(feedback.rate_question, question, user.uid, -1)

        with pytest.raises(RuntimeError):
            await accounts.delete_account(user)

        return await transaction(feedback.my_question_rating, question, user.uid)

    assert run(scenario()) == -1
    assert signed_out == []
