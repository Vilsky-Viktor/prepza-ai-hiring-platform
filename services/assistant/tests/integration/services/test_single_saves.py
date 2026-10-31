"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the retry (library's, or the user's) finds the whole action
still to do."""

import uuid

import pytest
from testee_common.auth.user import User

from assistant.core.db import Session
from assistant.repositories import conversations, messages, oauth
from assistant.schemas.chat import ChatRequest
from assistant.services import accounts, turns
from tests.integration.transactions import transaction


async def broken(*args, **kwargs):
    raise RuntimeError("The database went away")


async def conversations_of(user_id: str) -> list:
    async with Session() as session:
        return await conversations.of_user(session, user_id, None, 0, 100)


def test_an_account_deletion_whose_last_step_fails_keeps_the_users_conversations(run, monkeypatch):
    """The conversations and the connected AI apps go together: a failure leaves both for
    library's retry."""
    user = f"u-{uuid.uuid4()}"
    monkeypatch.setattr(oauth, "delete_user", broken)

    async def scenario():
        await transaction(conversations.create, user, None, "Kept")

        with pytest.raises(RuntimeError):
            await accounts.delete_user(user)

        return await conversations_of(user)

    assert [item.title for item in run(scenario())] == ["Kept"]


def test_a_new_conversation_is_saved_with_its_question_or_not_at_all(run, monkeypatch):
    """The new conversation, the chat from before signing in and the question are one save:
    when the question can't be saved, no conversation is left without it."""
    user = User(uid=f"u-{uuid.uuid4()}", email="ann@example.com", email_verified=True)
    body = ChatRequest(message="Create a company", earlier=[{"role": "user", "content": "Hi"}])

    async def no_companies(user_id, fresh=False):
        return frozenset()

    monkeypatch.setattr(turns, "user_companies", no_companies)
    monkeypatch.setattr(messages, "add_question", broken)

    async def scenario():
        with pytest.raises(RuntimeError):
            await turns.start(body, user, "token", "en")

        return await conversations_of(user.uid)

    assert run(scenario()) == []
