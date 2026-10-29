"""A conversation through the routes: a real database and Redis, companies answering as a
throwaway Auth emulator user, and a scripted model instead of OpenAI."""

import json
import os
import uuid

import httpx
from event_pushes import push
from langchain_core.messages import ToolMessage
from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer
from sqlalchemy import select

from assistant.core.db import Session
from assistant.integrations import llm
from assistant.main import app
from assistant.models.conversations import ToolCall
from assistant.repositories import conversations, messages
from tests.fake_model import FakeModel, calls, text
from tests.integration.transactions import transaction

PAGE = {"key": "companies", "path": "/companies"}
SETTINGS = {"key": "settings", "path": "/settings"}


def events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://assistant")


def library() -> dict:
    """A signed service token, as accounts calls to export a user's data."""
    token = issue_token("library", "assistant", os.environ["SERVICE_SECRET"])

    return bearer(token)


def test_a_conversation_is_streamed_saved_listed_exported_and_deleted(run, user, monkeypatch):
    uid, token = user
    model = FakeModel(
        calls(("list_companies", {})), text("You have no companies yet."), text("Still none.")
    )
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)
    headers = {"Authorization": f"Bearer {token}", "Accept-Language": "en"}

    async def scenario():
        async with client() as api:
            body = {"message": "My companies?", "page": PAGE}
            first = events((await api.post("/chat", json=body, headers=headers)).text)
            conversation_id = first[0]["conversation"]["id"]
            body = {"conversation_id": conversation_id, "message": "And now?", "page": SETTINGS}
            second = events((await api.post("/chat", json=body, headers=headers)).text)
            listed = (await api.get("/conversations", headers=headers)).json()
            opened = (await api.get(f"/conversations/{conversation_id}", headers=headers)).json()
            stored = await transaction(messages.recent, uuid.UUID(conversation_id), 20)
            calls = await tool_calls_of(stored[1].id)
            body = {"email": "ann@example.com"}
            exported = await api.post(f"/internal/users/{uid}/export", json=body, headers=library())
            gone = push("user.deleted", {"user_id": uid, "email": body["email"]}, uid)
            deleted = await api.post("/internal/events", json=gone)
            after = (await api.get("/conversations", headers=headers)).json()

            return first, second, listed, opened, stored, calls, exported.json(), deleted, after

    first, second, listed, opened, stored, await_calls, exported, deleted, after = run(scenario())

    assert [list(event) for event in first] == [
        ["conversation"],
        ["tool"],
        ["tool"],
        # A read shows nothing itself.
        *[["delta"]] * 5,
        ["done"],
        # The first answer brings the conversation's title.
        ["title"],
    ]
    assert first[2]["tool"]["state"] == "done"
    assert second[-1]["done"]["message_id"] == opened["messages"][-1]["id"]
    # The second turn's model reads the stored text only: tools' data isn't kept.
    assert not [m for m in model.prompts[2] if isinstance(m, ToolMessage)]
    # Each question is kept with the page it was asked on; the next turn reads the earlier one
    # with its page, and is on its own page.
    assert (stored[0].page, stored[2].page) == (PAGE, SETTINGS)
    assert model.prompts[2][1].content.startswith('[Asked on the page "companies" ')
    # The page it's asked on now opens the new message, in its context.
    assert 'the page "settings"' in model.prompts[2][-1].content
    assert first[-1] == {"title": "Your companies"}
    assert [item["title"] for item in listed] == ["Your companies"]
    assert [(m["role"], m["content"], m["status"]) for m in opened["messages"]] == [
        ("user", "My companies?", "complete"),
        ("assistant", "You have no companies yet.", "complete"),
        ("user", "And now?", "complete"),
        ("assistant", "Still none.", "complete"),
    ]
    answer = stored[1]
    # The two model calls' and the routing call's (tests/fake_model.py).
    assert (answer.input_tokens, answer.output_tokens) == (20 + 7, 10 + 3)
    # Which tool, how it ended: never its arguments' values or its result.
    [call] = await_calls
    assert (call.tool, call.status_code, call.state, call.arguments, call.result) == (
        "list_companies",
        200,
        "done",
        [],
        None,
    )
    assert answer.blocks == []
    [conversation] = exported["assistant_conversations"]
    assert len(conversation["messages"]) == 4
    # The text, and the blocks as references: never what the tools read.
    assert conversation["messages"][1]["blocks"] == []
    assert "result" not in json.dumps(exported)
    assert deleted.status_code == 204
    assert after == []


async def tool_calls_of(message_id) -> list[ToolCall]:
    async with Session() as session:
        return list(
            await session.scalars(select(ToolCall).where(ToolCall.message_id == message_id))
        )


def test_a_company_the_user_cant_see_is_refused_and_a_stored_one_is_deleted(run, user):
    uid, token = user
    headers = bearer(token)
    company_id = uuid.uuid4()

    async def scenario():
        # Stored while the user could see it; they've since lost access.
        stored = await transaction(conversations.create, uid, company_id, "Old")

        async with client() as api:
            body = {"message": "Hi", "company_id": str(company_id)}
            started = await api.post("/chat", json=body, headers=headers)
            opened = await api.get(f"/conversations/{stored.id}", headers=headers)

        return started, opened, await transaction(conversations.owned, stored.id, uid)

    started, opened, left = run(scenario())

    assert (started.status_code, started.json()["detail"]) == (404, "Company not found")
    assert opened.status_code == 404
    assert left is None


def test_someone_elses_conversation_is_not_found(run, user):
    _, token = user
    headers = bearer(token)

    async def scenario():
        other = await transaction(conversations.create, "someone-else", None, "Theirs")

        async with client() as api:
            opened = await api.get(f"/conversations/{other.id}", headers=headers)
            deleted = await api.delete(f"/conversations/{other.id}", headers=headers)

        return opened, deleted, await transaction(conversations.owned, other.id, "someone-else")

    opened, deleted, kept = run(scenario())

    assert (opened.status_code, deleted.status_code) == (404, 404)
    assert kept is not None
