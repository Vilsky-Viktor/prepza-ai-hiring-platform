import asyncio
import json
import uuid

import httpx
import pytest
from fastapi import HTTPException

from app.constants.actions_flow import ACTION_TTL_SECONDS
from app.integrations import services
from app.services import actions, chat
from app.services.registry import tools
from app.storage import actions as store
from tests.unit.actions_setup import ANN, BOB, COMPANY, CONVERSATION, TURN, prepared


def test_preparing_runs_nothing_and_keeps_the_action_in_redis_for_ten_minutes(redis, writes):
    action_id = prepared(redis)
    kept = json.loads(redis.counts[store.key(action_id)])

    assert writes == []
    assert {key: kept[key] for key in ("user_id", "conversation_id", "company_id", "tool")} == {
        "user_id": "ann",
        "conversation_id": str(CONVERSATION),
        "company_id": None,
        "tool": "create_company",
    }
    assert kept["arguments"] == {"name": "Acme"}
    assert kept["card"]["preview"] == {"name": "Acme"}
    assert redis.expiries[store.key(action_id)] == ACTION_TTL_SECONDS == 600


def test_a_card_shows_exactly_what_runs():
    block = actions.card(uuid.uuid4(), tools()["create_company"], {"name": "Acme"}, "pending")

    assert (block["kind"], block["tool"], block["preview"]) == (
        "confirm",
        "create_company",
        {"name": "Acme"},
    )
    assert block["destructive"] is False


def test_a_confirmed_action_runs_once_as_the_user_and_a_second_confirm_finds_it_gone(redis, writes):
    action_id = prepared(redis)
    *_, block = asyncio.run(actions.run(CONVERSATION, action_id, ANN, "fresh", "en"))

    assert writes == [
        ("companies", "POST", "/companies", {"name": "Acme"}, "fresh", str(action_id))
    ]
    assert (block["state"], block["links"]) == ("done", [f"/companies/{COMPANY}/interviews"])
    assert store.key(action_id) not in redis.counts

    with pytest.raises(HTTPException) as again:
        asyncio.run(actions.run(CONVERSATION, action_id, ANN, "fresh", "en"))

    assert again.value.status_code == 409
    assert len(writes) == 1


def test_two_confirms_at_once_run_it_once(redis, writes):
    action_id = prepared(redis)

    async def both():
        return await asyncio.gather(
            actions.run(CONVERSATION, action_id, ANN, "t", "en"),
            actions.run(CONVERSATION, action_id, ANN, "t", "en"),
            return_exceptions=True,
        )

    outcomes = asyncio.run(both())

    assert len(writes) == 1
    assert sum(isinstance(outcome, HTTPException) for outcome in outcomes) == 1


@pytest.mark.parametrize("user, conversation", [(BOB, CONVERSATION), (ANN, uuid.uuid4())])
def test_only_its_user_in_its_conversation_may_confirm_it(redis, writes, user, conversation):
    action_id = prepared(redis)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(actions.run(conversation, action_id, user, "t", "en"))

    assert refused.value.status_code == 404
    assert writes == []
    # Still there for its own user.
    assert store.key(action_id) in redis.counts


def test_a_company_no_longer_the_users_is_refused_on_confirm(redis, writes, monkeypatch):
    async def get(service, path, query, token, language, via=None):
        return httpx.Response(200, json={"name": "Acme"}, request=httpx.Request("GET", "http://x"))

    monkeypatch.setattr(services, "get", get)
    arguments = {"company_id": COMPANY, "title": "Acme 2"}
    result = asyncio.run(actions.prepare(tools()["rename_company"], arguments, TURN))
    assert result.block["subject"] == "Acme"

    async def none_left(user_id, fresh=False):
        return frozenset()

    monkeypatch.setattr(actions, "user_companies", none_left)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(actions.run(CONVERSATION, result.action_id, ANN, "t", "en"))

    assert refused.value.status_code == 404
    assert writes == []


def test_an_expired_or_cancelled_action_is_gone(redis, writes):
    action_id = prepared(redis)
    asyncio.run(actions.cancel(CONVERSATION, action_id, ANN, "t", "en"))

    with pytest.raises(HTTPException):
        asyncio.run(actions.run(CONVERSATION, action_id, ANN, "t", "en"))

    expired = prepared(redis)
    # Redis drops it after ACTION_TTL_SECONDS.
    redis.counts.pop(store.key(expired))

    with pytest.raises(HTTPException) as gone:
        asyncio.run(actions.run(CONVERSATION, expired, ANN, "t", "en"))

    assert gone.value.status_code == 409
    assert writes == []


def test_a_refused_token_runs_nothing_and_keeps_the_action_for_a_fresh_one(redis, writes):
    action_id = prepared(redis)
    writes.status = 401

    with pytest.raises(HTTPException) as refused:
        asyncio.run(actions.run(CONVERSATION, action_id, ANN, "stale", "en"))

    assert refused.value.status_code == 401
    assert store.key(action_id) in redis.counts


def test_a_tool_naming_another_company_is_refused_before_anything_is_called(monkeypatch):
    called = []

    async def call_tools(calls, token, language, company_id):
        called.extend(calls)

        return []

    monkeypatch.setattr(chat, "call_tools", call_tools)
    other = {"company_id": "00000000-0000-0000-0000-000000000000"}
    [result] = asyncio.run(chat.step_results([("get_company", other)], TURN))

    assert called == []
    assert result.content["error"] == 404


def test_signing_out_tells_the_panel_to_and_calls_nothing(monkeypatch):
    called = []

    async def call_tools(calls, token, language, company_id):
        called.extend(calls)

        return []

    monkeypatch.setattr(chat, "call_tools", call_tools)
    [result] = asyncio.run(chat.step_results([("sign_out", {})], TURN))
    assert called == []
    assert result.block is None

    emitted = []
    answer = chat.Answer()
    call = {"name": "sign_out", "args": {}, "id": "c1", "type": "tool_call"}
    asyncio.run(chat.run_tools([call], TURN, answer, emitted.append))

    assert {"sign_out": True} in emitted
    assert answer.blocks == []


def test_a_done_card_names_what_the_action_made(redis, writes):
    action_id = prepared(redis)
    *_, block = asyncio.run(actions.run(CONVERSATION, action_id, ANN, "t", "en"))

    assert block["result_label"] == "Acme"


def test_a_company_made_by_the_assistant_counts_for_the_referral_link(redis, writes):
    """The referral cookie of the user's browser goes with it, as on the site."""
    action_id = prepared(redis)
    asyncio.run(actions.run(CONVERSATION, action_id, ANN, "fresh", "en", "abc123"))

    assert writes.referrals == ["abc123"]


def test_a_confirm_the_message_limits_refuse_isnt_counted_as_an_action(redis, writes, monkeypatch):
    counted = []

    async def over(redis, user_id, company_id):
        raise HTTPException(429, "Too many messages")

    async def count(redis, user_id, company_id=None):
        counted.append(user_id)

    monkeypatch.setattr(actions.limits, "check", over)
    monkeypatch.setattr(actions, "count_action", count)
    action_id = prepared(redis)

    with pytest.raises(HTTPException):
        asyncio.run(actions.run(CONVERSATION, action_id, ANN, "fresh", "en"))

    assert (counted, writes) == ([], [])
