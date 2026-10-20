"""A delegated turn through the routes (ASSISTANT_MODE=subagents): a real database and Redis,
companies answering as a throwaway Auth emulator user, and a scripted model. The company's agent
prepares the card as the user; it reaches the panel and comes back with the answer, and only the
delegate's name is stored, never its brief."""

import json
import uuid

import httpx
from sqlalchemy import select

from app.config.settings import settings
from app.constants.subagents import AssistantMode
from app.integrations import llm
from app.main import app
from app.models.conversations import ToolCall
from app.storage.db import Session
from tests.fake_model import FakeModel, calls

BRIEF = {"task": "Create the company Delegated Ltd", "company_id": None, "interview_id": None}


def events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


async def stored_calls(message_id: str) -> list[ToolCall]:
    async with Session() as session:
        found = await session.scalars(
            select(ToolCall).where(ToolCall.message_id == uuid.UUID(message_id))
        )

        return list(found)


def test_a_domain_agent_prepares_the_card_the_panel_shows(run, user, monkeypatch):
    _, token = user
    monkeypatch.setattr(settings, "assistant_mode", AssistantMode.SUBAGENTS)
    model = FakeModel(
        calls(("delegate_company", BRIEF)), calls(("create_company", {"name": "Delegated Ltd"}))
    )
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)
    headers = {"Authorization": f"Bearer {token}", "Accept-Language": "en"}
    transport = httpx.ASGITransport(app=app)

    async def scenario():
        async with httpx.AsyncClient(transport=transport, base_url="http://assistant") as api:
            body = {"message": "Create the company Delegated Ltd"}
            asked = events((await api.post("/chat", json=body, headers=headers)).text)
            conversation_id = asked[0]["conversation"]["id"]
            opened = (await api.get(f"/conversations/{conversation_id}", headers=headers)).json()
            answer_id = opened["messages"][-1]["id"]
            tools = [(call.tool, call.arguments) for call in await stored_calls(answer_id)]

        return asked, opened, tools

    asked, opened, tools = run(scenario())

    [card] = [event["block"] for event in asked if "block" in event]
    assert (card["kind"], card["state"], card["preview"]) == (
        "confirm",
        "pending",
        {"name": "Delegated Ltd"},
    )
    # The domain agent's text never reached the panel; the turn ended with the card.
    assert not [event for event in asked if "delta" in event]
    assert [event for event in asked if "done" in event]
    assert [block["action_id"] for block in opened["messages"][-1]["blocks"]] == [card["action_id"]]
    # The company's agent was offered its own tools, never the main agent's delegates.
    names = [tool["function"]["name"] for tool in model.bound[1][0]]
    assert "create_company" in names and "delegate_company" not in names
    assert tools == [("delegate_company", [])]
