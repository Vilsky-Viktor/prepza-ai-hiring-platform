"""Retention, company.deleted and the limits against the real database and Redis."""

import uuid
from datetime import UTC, datetime, timedelta

from event_pushes import push
import httpx
import pytest
from fastapi import HTTPException
from prepza_common.limits.limit_list import LIMITS_KEY
from prepza_common.redis import memory_cache
from sqlalchemy import update

from assistant.core.db import Session
from assistant.integrations.redis import get_redis
from assistant.main import app
from assistant.models.conversations import Conversation, Message
from assistant.repositories import conversations, messages
from assistant.schemas.chat import EarlierTurn
from assistant.services import limits, retention
from tests.integration.transactions import transaction


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://assistant")


async def idle_since(conversation_id, days: int) -> None:
    async with Session() as session:
        await session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.now(UTC) - timedelta(days=days))
        )
        await session.commit()


def test_retention_deletes_idle_conversations_in_batches_and_is_safe_to_repeat(run, monkeypatch):
    monkeypatch.setattr(retention, "RETENTION_BATCH", 2)
    user = f"retention-{uuid.uuid4().hex[:8]}"

    async def scenario():
        old = [await transaction(conversations.create, user, None, f"old {i}") for i in range(5)]
        recent = await transaction(conversations.create, user, None, "recent")

        for conversation in old:
            await idle_since(conversation.id, 91)

        await idle_since(recent.id, 89)

        async with client() as api:
            first = await api.post("/internal/schedules/retention")
            again = await api.post("/internal/schedules/retention")

        left = await transaction(conversations.of_user, user, None, 0, 100)

        return first, again, left

    first, again, left = run(scenario())

    assert (first.status_code, again.status_code) == (204, 204)
    assert [item.title for item in left] == ["recent"]


def test_company_deleted_deletes_its_conversations_once_and_again_changes_nothing(run):
    gone, other = uuid.uuid4(), uuid.uuid4()
    user = f"members-{uuid.uuid4().hex[:8]}"

    async def scenario():
        await transaction(conversations.create, user, gone, "About the gone company")
        await transaction(conversations.create, user, other, "About another")
        await transaction(conversations.create, user, None, "About none")
        event = push("company.deleted", {"company_id": str(gone)})

        async with client() as api:
            answers = [(await api.post("/internal/events", json=event)).status_code for _ in "12"]

        return answers, await transaction(conversations.of_user, user, None, 0, 100)

    answers, left = run(scenario())

    assert answers == [204, 204]
    assert sorted(item.title for item in left) == ["About another", "About none"]


def test_the_limits_count_in_redis_at_their_edited_values(run, published, monkeypatch):
    user = f"limits-{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(memory_cache, "_entries", {})

    async def scenario():
        redis = get_redis()
        # As billing keeps the values edited in the admin zone.
        await redis.hset(
            LIMITS_KEY, mapping={"MESSAGES_PER_USER_HOUR": 3, "TOKENS_PER_USER_DAY": 10_000}
        )

        try:
            for _ in range(3):
                await limits.check(redis, user, None)

            with pytest.raises(HTTPException) as over_messages:
                await limits.check(redis, user, None)

            spender = f"{user}-spender"
            await limits.check(redis, spender, None)
            await limits.record(redis, spender, None, 10_001)

            with pytest.raises(HTTPException) as over_budget:
                await limits.check(redis, spender, None)
        finally:
            # Everyone's totals, so repeated runs don't fill them.
            await redis.delete(LIMITS_KEY, "spend:assistant:all", "rate:assistant:all")

        return over_messages.value.status_code, over_budget.value.status_code

    assert run(scenario()) == (429, 429)
    hits = [(data["limit"], data["user_id"]) for kind, data in published if kind == "limit.hit"]
    assert hits == [("MESSAGES_PER_USER_HOUR", user), ("TOKENS_PER_USER_DAY", f"{user}-spender")]


def test_a_visitors_chat_starts_the_new_conversation_in_its_order(run):
    user = f"earlier-{uuid.uuid4().hex[:8]}"
    turns = [
        EarlierTurn(role="user", content="What is prepza?"),
        EarlierTurn(role="assistant", content="A hiring test."),
        EarlierTurn(role="user", content="How much?"),
        EarlierTurn(role="assistant", content="$1–3 a candidate."),
    ]

    async def scenario():
        conversation = await transaction(conversations.create, user, None, "Sign in")
        await transaction(messages.add_earlier, conversation.id, turns)
        await transaction(messages.add_question, conversation.id, "Create a company", "text")

        return await transaction(messages.recent, conversation.id, 20)

    found = run(scenario())

    assert [(message.role, message.content) for message in found] == [
        *[(turn.role, turn.content) for turn in turns],
        ("user", "Create a company"),
    ]


def test_an_erased_candidates_or_deleted_interviews_conversations_go_and_the_rest_stay(run):
    company, other = uuid.uuid4(), uuid.uuid4()
    user = f"members-{uuid.uuid4().hex[:8]}"
    interview = str(uuid.uuid4())

    async def say(company_id, title, content):
        conversation = await transaction(conversations.create, user, company_id, title)
        await transaction(messages.add_question, conversation.id, content, "text")

    async def scenario():
        await say(company, "Asked about Ann", "How did ANN@example.com do?")
        await say(company, "About the interview", f"Open /interviews/{interview}")
        await say(company, "About Bo", "How did bo@example.com do?")
        # Another company's conversation about the same address isn't this company's to erase.
        await say(other, "Ann elsewhere", "ann@example.com")
        removed = push(
            "candidate.removed",
            {"company_id": str(company), "interview_id": interview, "email": "ann@example.com"},
        )
        deleted = push(
            "candidate.interview_deleted",
            {"company_id": str(company), "interview_id": interview},
        )

        async with client() as api:
            for event in (removed, removed, deleted):
                assert (await api.post("/internal/events", json=event)).status_code == 204

        return await transaction(conversations.of_user, user, None, 0, 100)

    left = run(scenario())

    assert sorted(item.title for item in left) == ["About Bo", "Ann elsewhere"]


def test_an_accounts_answers_traces_are_found_to_delete_with_it(run):
    user, other = f"traced-{uuid.uuid4().hex[:8]}", f"other-{uuid.uuid4().hex[:8]}"

    async def scenario():
        for owner, trace in ((user, "a" * 32), (other, "b" * 32)):
            conversation = await transaction(conversations.create, owner, None, "Traced")
            await transaction(messages.add_question, conversation.id, "Hi", "text")

            async with Session() as session:
                await session.execute(
                    update(Message)
                    .where(Message.conversation_id == conversation.id)
                    .values(trace_id=trace)
                )
                await session.commit()

        return await transaction(conversations.trace_ids_of_user, user)

    assert run(scenario()) == ["a" * 32]


def test_a_companys_conversations_go_batch_after_batch(run, monkeypatch):
    from prepza_common.db import db

    monkeypatch.setattr(db, "DELETE_BATCH", 2)
    company, other = uuid.uuid4(), uuid.uuid4()
    user = f"members-{uuid.uuid4().hex[:8]}"

    async def scenario():
        for number in range(3):
            about = await transaction(conversations.create, user, company, f"Ann {number}")
            await transaction(
                messages.add_question, about.id, "How did ann@example.com do?", "text"
            )

        for number in range(3):
            await transaction(conversations.create, user, company, f"Bo {number}")

        await transaction(conversations.create, user, other, "Elsewhere")
        mentioned = await conversations.delete_mentioning(Session, company, ["ann@example.com"])
        after_mentions = await transaction(conversations.of_user, user, None, 0, 100)
        deleted = await conversations.delete_company(Session, company)
        left = await transaction(conversations.of_user, user, None, 0, 100)
        await transaction(conversations.delete_user, user)

        return mentioned, after_mentions, deleted, left

    mentioned, after_mentions, deleted, left = run(scenario())

    # More than a batch each time, all gone; another company's stays.
    assert mentioned == 3
    assert sorted(item.title for item in after_mentions) == ["Bo 0", "Bo 1", "Bo 2", "Elsewhere"]
    assert deleted == 3
    assert [item.title for item in left] == ["Elsewhere"]
