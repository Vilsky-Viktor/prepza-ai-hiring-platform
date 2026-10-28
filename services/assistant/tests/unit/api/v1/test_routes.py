import asyncio
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException
from prepza_common.auth.user import User

from assistant.api.dependencies import user_with_token
from assistant.api.v1 import chat as chat_router
from assistant.api.v1 import conversations as conversations_router
from assistant.constants.limits import MAX_AUDIO_SECONDS
from assistant.integrations import services
from assistant.main import app
from assistant.models.conversations import Conversation
from assistant.repositories import conversations, messages
from assistant.services import conversations as conversation_service
from assistant.services import turns

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
ANN = User(uid="ann", email="ann@example.com", email_verified=True)
# The answer a vote names: (conversation, message).
VOTED = (uuid.uuid4(), uuid.uuid4())


@pytest.fixture
def signed_in():
    app.dependency_overrides[user_with_token] = lambda: (ANN, "user-token")

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def created(monkeypatch):
    """Conversations created; none must be when a message is refused."""
    made = []

    async def create(user_id, company_id, title):
        made.append((user_id, company_id, title))

    monkeypatch.setattr(conversations, "create", create)

    return made


def companies_answers(monkeypatch, status):
    async def get(service, path, query, token, language, via=None):
        return httpx.Response(status, json={}, request=httpx.Request("GET", "http://companies"))

    monkeypatch.setattr(services, "get", get)


def test_a_message_too_long_is_refused_in_the_users_language(client, signed_in):
    response = client.post(
        "/chat", json={"message": "x" * 2_001}, headers={"Accept-Language": "de"}
    )

    assert response.status_code == 422
    assert "Die Frage ist zu lang." in response.text


def test_paused_or_over_a_limit_is_refused_before_anything_is_saved(
    client, signed_in, created, monkeypatch
):
    async def paused(redis, what, company_id=None, user_id=None):
        raise HTTPException(503, "paused")

    monkeypatch.setattr(turns, "refuse_if_paused", paused)
    assert client.post("/chat", json={"message": "Hi"}).status_code == 503

    async def over(redis, user_id, company_id):
        raise HTTPException(429, "over")

    async def not_paused(redis, what, company_id=None, user_id=None):
        pass

    async def companies(user_id, fresh=False):
        return frozenset()

    monkeypatch.setattr(turns, "refuse_if_paused", not_paused)
    monkeypatch.setattr(turns, "user_companies", companies)
    monkeypatch.setattr(turns.limits, "check", over)
    assert client.post("/chat", json={"message": "Hi"}).status_code == 429
    assert created == []


def test_a_new_conversation_only_about_a_company_the_user_can_see(
    client, signed_in, created, monkeypatch
):
    async def not_paused(redis, what, company_id=None, user_id=None):
        pass

    async def companies(user_id, fresh=False):
        return frozenset({"another-company"})

    monkeypatch.setattr(turns, "refuse_if_paused", not_paused)
    monkeypatch.setattr(turns, "user_companies", companies)
    response = client.post("/chat", json={"message": "Hi", "company_id": str(COMPANY)})

    assert (response.status_code, response.json()["detail"]) == (404, "Company not found")
    assert created == []


def test_the_panel_reads_its_limits_signed_out_too(client, monkeypatch):
    monkeypatch.setattr(chat_router, "get_redis", lambda: FakeRedis())
    config = client.get("/config").json()

    assert config["restore_minutes"] == 30
    assert config["max_message_length"] == 2_000
    assert config["max_audio_seconds"] == MAX_AUDIO_SECONDS
    assert (config["messages_per_hour"], config["messages_per_day"]) == (30, 200)


def test_the_panel_reads_the_message_limits_as_edited(client, monkeypatch):
    edited = FakeRedis({"MESSAGES_PER_USER_HOUR": 12, "MESSAGES_PER_USER_DAY": 90})
    monkeypatch.setattr(chat_router, "get_redis", lambda: edited)
    config = client.get("/config").json()

    assert (config["messages_per_hour"], config["messages_per_day"]) == (12, 90)


def test_signed_out_and_unsigned_calls_are_refused(client):
    assert client.post("/chat", json={"message": "Hi"}).status_code in (401, 403)
    assert client.get("/conversations").status_code in (401, 403)
    response = client.request("DELETE", "/internal/users/ann", json={"email": "a@b.c"})
    assert response.status_code in (401, 403)
    forged = {"Authorization": "Bearer forged"}
    response = client.post("/internal/users/ann/export", json={"email": "a@b.c"}, headers=forged)
    assert response.status_code == 401


@pytest.mark.parametrize("status, kept", [(200, True), (403, False), (404, False)])
def test_a_conversation_about_a_company_lost_to_the_user_is_deleted_on_opening(
    monkeypatch, status, kept
):
    conversation = Conversation(id=uuid.uuid4(), user_id="ann", company_id=COMPANY, title="t")
    deleted = []

    async def owned(conversation_id, user_id):
        return conversation

    async def delete_one(conversation_id):
        deleted.append(conversation_id)

    monkeypatch.setattr(conversations, "owned", owned)
    monkeypatch.setattr(conversations, "delete_one", delete_one)
    companies_answers(monkeypatch, status)
    opening = conversation_service.open_conversation(conversation.id, "ann", "token", "en")

    if kept:
        assert asyncio.run(opening) is conversation
        assert deleted == []
    else:
        with pytest.raises(HTTPException) as error:
            asyncio.run(opening)

        assert error.value.status_code == 404
        assert deleted == [conversation.id]


def test_companies_failing_is_a_503_not_a_deletion(monkeypatch):
    companies_answers(monkeypatch, 502)

    with pytest.raises(HTTPException) as error:
        asyncio.run(conversation_service.has_access(COMPANY, "token", "en"))

    assert error.value.status_code == 503


def test_a_visitors_earlier_chat_is_cut_to_a_messages_length_and_limited_in_count(
    client, signed_in
):
    from assistant.schemas.chat import ChatRequest

    body = ChatRequest(message="Hi", earlier=[{"role": "assistant", "content": "x" * 3_000}])
    assert len(body.earlier[0].content) == 2_000

    too_many = [{"role": "user", "content": "Hi"}] * 21
    response = client.post("/chat", json={"message": "Hi", "earlier": too_many})
    assert response.status_code == 422


def test_only_a_recent_conversation_is_brought_back(client, signed_in, monkeypatch):
    windows = []

    async def latest(user_id, minutes):
        windows.append((user_id, minutes))

        return latest.found

    latest.found = None
    monkeypatch.setattr(conversations, "latest", latest)
    assert client.get("/conversations/active").status_code == 204

    latest.found = Conversation(
        id=uuid.uuid4(),
        user_id="ann",
        company_id=None,
        title="Hi",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    response = client.get("/conversations/active")
    assert response.json()["id"] == str(latest.found.id)
    assert windows == [("ann", 30), ("ann", 30)]


@pytest.fixture
def voted(monkeypatch):
    """Votes saved, as (conversation, user, message, vote), on an answer that's the user's when
    `owned`; and the traces sent on to Langfuse."""
    saved, mirrored = [], []
    state = {"owned": True, "trace": "a" * 32}

    async def set_vote(conversation_id, user_id, message_id, vote):
        saved.append((conversation_id, user_id, message_id, vote))

        return state["owned"], state["trace"] if state["owned"] else None

    monkeypatch.setattr(messages, "set_vote", set_vote)

    async def mirror_vote(trace_id, current):
        mirrored.append(trace_id)

    monkeypatch.setattr(conversations_router, "mirror_vote", mirror_vote)

    return saved, mirrored, state


def vote_path():
    return f"/conversations/{VOTED[0]}/messages/{VOTED[1]}/vote"


@pytest.mark.parametrize("value", [1, -1, None])
def test_the_owner_votes_changes_or_clears_their_vote(client, signed_in, voted, value):
    saved, mirrored, state = voted

    assert client.put(vote_path(), json={"value": value}).status_code == 204
    assert saved == [(VOTED[0], "ann", VOTED[1], value)]
    assert mirrored == [state["trace"]]


def test_an_answer_not_in_the_users_own_conversation_is_not_found(client, signed_in, voted):
    _, mirrored, state = voted
    state["owned"] = False

    response = client.put(vote_path(), json={"value": 1})

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"
    assert mirrored == []


@pytest.mark.parametrize("value", [0, 2, "up"])
def test_only_a_thumbs_up_or_down_is_taken(client, signed_in, voted, value):
    assert client.put(vote_path(), json={"value": value}).status_code == 422
    assert voted[0] == []


def test_signed_out_nobody_votes(client, voted):
    assert client.put(vote_path(), json={"value": 1}).status_code == 401
    assert voted[0] == []
