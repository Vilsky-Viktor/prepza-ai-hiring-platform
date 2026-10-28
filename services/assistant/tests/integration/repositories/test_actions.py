"""Actions against a real Redis, and one confirmed through the routes against the real
companies service, as a throwaway Auth emulator user (a scripted model instead of OpenAI)."""

import asyncio
import json
import uuid

import httpx
from sqlalchemy import select

from assistant.constants.actions_flow import ACTION_TTL_SECONDS
from assistant.core.db import Session
from assistant.integrations import llm, services
from assistant.integrations.redis import get_redis
from assistant.main import app
from assistant.models.conversations import ToolCall
from assistant.repositories import actions
from tests.fake_model import FakeModel, calls, text


def events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://assistant")


def test_redis_hands_a_pending_action_to_one_claim_only_and_expires_it(run):
    action_id = uuid.uuid4()
    pending = {"user_id": f"u-{action_id.hex[:6]}", "conversation_id": "c", "tool": "t"}

    async def scenario():
        await actions.save(action_id, pending)
        ttl = await get_redis().ttl(actions.key(action_id))
        claims = await asyncio.gather(*(actions.claim(action_id) for _ in range(5)))
        left = await actions.peek(action_id)

        return ttl, claims, left

    ttl, claims, left = run(scenario())

    assert 0 < ttl <= ACTION_TTL_SECONDS
    assert [claim for claim in claims if claim] == [pending]
    assert left is None


def test_deleting_an_account_deletes_its_pending_actions(run):
    user_id = f"gone-{uuid.uuid4().hex[:6]}"
    ids = [uuid.uuid4(), uuid.uuid4()]

    async def scenario():
        for action_id in ids:
            await actions.save(action_id, {"user_id": user_id, "conversation_id": "c"})

        await actions.delete_user(user_id)

        return [await actions.peek(action_id) for action_id in ids]

    assert run(scenario()) == [None, None]


def test_a_confirmed_company_is_created_once_as_the_user_and_nothing_of_it_is_stored(
    run, user, monkeypatch
):
    _, token = user
    name = f"Assistant {uuid.uuid4().hex[:6]}"
    model = FakeModel(
        calls(("create_company", {"name": name})),
        text("Check the card and confirm it below."),
        text(f"Created {name}."),
    )
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)
    headers = {"Authorization": f"Bearer {token}", "Accept-Language": "en"}

    async def scenario():
        async with client() as api:
            asked = events(
                (await api.post("/chat", json={"message": f"Create {name}"}, headers=headers)).text
            )
            conversation_id = asked[0]["conversation"]["id"]
            [card] = [event["block"] for event in asked if "block" in event]
            path = f"/conversations/{conversation_id}/actions/{card['action_id']}"
            confirmed = await api.post(f"{path}/confirm", headers=headers)
            again = await api.post(f"{path}/confirm", headers=headers)
            listed = await services.get("companies", "/companies", {}, token, "en")
            mine = [item for item in listed.json() if item["name"] == name]

            for company in mine:
                await services.send(
                    "companies", "DELETE", f"/companies/{company['id']}", {}, None, token, "en"
                )

            async with Session() as session:
                stored = list(await session.scalars(select(ToolCall)))

        return card, events(confirmed.text), again.status_code, mine, stored

    card, confirmed, again, mine, stored = run(scenario())

    assert (card["kind"], card["state"], card["preview"]) == ("confirm", "pending", {"name": name})
    assert confirmed[1]["action"]["state"] == "done"
    assert confirmed[1]["action"]["links"] == [f"/companies/{mine[0]['id']}/interviews"]
    assert confirmed[-1] == {"done": confirmed[-1]["done"]}
    assert again == 409
    assert len(mine) == 1
    # The action's arguments and result were never written to the database.
    assert all(name not in json.dumps(call.arguments) for call in stored)
    assert all(call.result is None for call in stored)


def test_a_pending_card_comes_back_with_its_answer_until_its_handled(run, user, monkeypatch):
    _, token = user
    model = FakeModel(calls(("create_company", {"name": "Later Ltd"})), text("Here it is:"))
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)
    headers = {"Authorization": f"Bearer {token}", "Accept-Language": "en"}

    async def scenario():
        async with client() as api:
            asked = events(
                (
                    await api.post("/chat", json={"message": "Create Later Ltd"}, headers=headers)
                ).text
            )
            conversation_id = asked[0]["conversation"]["id"]
            [card] = [event["block"] for event in asked if "block" in event]
            opened = (await api.get(f"/conversations/{conversation_id}", headers=headers)).json()
            path = f"/conversations/{conversation_id}/actions/{card['action_id']}"
            await api.post(f"{path}/cancel", headers=headers)
            after = (await api.get(f"/conversations/{conversation_id}", headers=headers)).json()

        return card, opened, after

    card, opened, after = run(scenario())

    answer = opened["messages"][-1]
    assert answer["role"] == "assistant"
    assert [block["action_id"] for block in answer["blocks"]] == [card["action_id"]]
    assert answer["blocks"][0]["preview"] == {"name": "Later Ltd"}
    assert after["messages"][-1]["blocks"] == []
