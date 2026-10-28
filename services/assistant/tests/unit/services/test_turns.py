import asyncio
import json
import uuid

import anyio
import httpx
import openai
import pytest
from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from prepza_common.auth.user import User
from prepza_common.http.sse import KEEP_ALIVE

from assistant.constants.chat import CHAT_FAILED, TURNS_AT_ONCE, TURNS_BUSY_RETRY_SECONDS, Status
from assistant.integrations import llm, services
from assistant.models.answers import Turn
from assistant.schemas.chat import ChatRequest
from assistant.services import turns
from tests.fake_model import FakeModel, calls, text

TURN = Turn(uuid.uuid4(), "ann", None, "user-token", "en")
MESSAGE_ID = uuid.uuid4()


class Saved(list):
    """The answers saved, as (status, content, tools), and the tokens recorded."""

    tokens: list


@pytest.fixture
def saved(monkeypatch):
    found = Saved()
    found.tokens = []

    async def add_answer(conversation_id, answer, status):
        found.append((status, answer.content, [result.tool for result in answer.results]))

        return MESSAGE_ID

    async def record(redis, user_id, company_id, tokens):
        found.tokens.append((user_id, tokens))

    async def get(service, path, query, token, language, via=None):
        return httpx.Response(
            200, json={"email": "ann@example.com"}, request=httpx.Request("GET", "http://x")
        )

    async def no_title(turn):
        return None

    monkeypatch.setattr(turns.messages, "add_answer", add_answer)
    monkeypatch.setattr(turns.titles, "refresh", no_title)
    monkeypatch.setattr(turns.limits, "record", record)
    monkeypatch.setattr(services, "get", get)

    return found


def script(monkeypatch, *replies) -> FakeModel:
    fake = FakeModel(*replies)
    monkeypatch.setattr(llm, "get_chat_model", lambda: fake)

    return fake


def events_of(chunks: list[str]) -> list:
    return [json.loads(chunk.removeprefix("data: ")) for chunk in chunks if chunk != KEEP_ALIVE]


def collect() -> list[str]:
    async def read():
        return [chunk async for chunk in turns.stream(TURN, [HumanMessage(content="Who am I?")])]

    return asyncio.run(read())


def test_a_turns_events_come_in_order_and_end_with_the_saved_message(monkeypatch, saved):
    script(monkeypatch, calls(("get_me", {})), text("You're Ann."))

    assert events_of(collect()) == [
        {"conversation": {"id": str(TURN.conversation_id)}},
        {"tool": {"name": "get_me", "state": "running", "label": "Reading your account…"}},
        {"tool": {"name": "get_me", "state": "done", "label": "Reading your account…"}},
        {"delta": "You're"},
        {"delta": " Ann."},
        {"done": {"message_id": str(MESSAGE_ID)}},
    ]
    assert saved == [(Status.COMPLETE, "You're Ann.", ["get_me"])]
    # The two model calls' tokens and the routing call's (tests/fake_model.py).
    assert saved.tokens == [("ann", 30 + 10)]


def test_a_quiet_stream_sends_keep_alives(monkeypatch, saved):
    monkeypatch.setattr(turns, "KEEP_ALIVE_SECONDS", 0.01)
    script(monkeypatch, text("Thinking slowly", sleep=0.1))

    chunks = collect()

    assert KEEP_ALIVE in chunks
    assert events_of(chunks)[-1] == {"done": {"message_id": str(MESSAGE_ID)}}


def test_a_turn_out_of_time_fails_and_keeps_its_text(monkeypatch, saved):
    monkeypatch.setattr(turns, "TURN_SECONDS", 0.05)
    script(monkeypatch, text("Partly done", sleep=5))

    events = events_of(collect())

    assert events[-1] == {"error": CHAT_FAILED}
    assert saved == [(Status.FAILED, "Partly", [])]


def test_a_failing_model_is_an_error_to_try_again(monkeypatch, saved):
    script(monkeypatch, RuntimeError("OpenAI is down"))

    assert events_of(collect())[-1] == {"error": CHAT_FAILED}
    assert saved == [(Status.FAILED, "", [])]


def test_openai_failing_is_logged_by_its_module_for_the_alert(monkeypatch, saved, caplog):
    """The "prepza OpenAI failing" alert counts errors naming "openai."; nothing of the
    conversation is logged."""
    failure = openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))
    script(monkeypatch, failure)

    collect()

    assert "An assistant turn failed: openai.APIConnectionError" in caplog.text
    assert "api.openai.com" not in caplog.text


def test_an_expired_session_says_so_with_its_code(monkeypatch, saved):
    async def refused(service, path, query, token, language, via=None):
        return httpx.Response(401, json={}, request=httpx.Request("GET", "http://x"))

    monkeypatch.setattr(services, "get", refused)
    script(monkeypatch, calls(("get_pause", {})))

    last = events_of(collect())[-1]

    assert last["code"] == "session_expired"
    assert saved[0][0] == Status.FAILED


def test_an_answer_that_cant_be_saved_is_an_error(monkeypatch, saved):
    async def gone(conversation_id, answer, status):
        raise RuntimeError("conversation deleted")

    monkeypatch.setattr(turns.messages, "add_answer", gone)
    script(monkeypatch, text("Hi"))

    assert events_of(collect())[-1] == {"error": CHAT_FAILED}


@pytest.mark.parametrize("how", ["cancel", "scope", "close"])
def test_a_stopped_turn_is_saved_cancelled_with_its_text_so_far(monkeypatch, saved, how):
    """The server cancels the request when the client goes (Starlette cancels its task group's
    scope, which cancels every await in it again), or closes the stream: the turn stops and
    saves what it had before the request ends."""
    script(monkeypatch, text("Half an answer", sleep=5))

    async def scenario():
        stream = turns.stream(TURN, [HumanMessage(content="Who am I?")])

        if how == "close":
            async for chunk in stream:
                if "delta" in chunk:
                    break

            await stream.aclose()

            return

        first_delta = asyncio.Event()

        async def read():
            async for chunk in stream:
                if "delta" in chunk:
                    first_delta.set()

        if how == "scope":
            async with anyio.create_task_group() as group:
                group.start_soon(read)
                await first_delta.wait()
                group.cancel_scope.cancel()

            return

        reading = asyncio.create_task(read())
        await first_delta.wait()
        reading.cancel()
        await asyncio.gather(reading, return_exceptions=True)

    asyncio.run(asyncio.wait_for(scenario(), 2))

    assert saved == [(Status.CANCELLED, "Half", [])]
    # Cut short, the call reported no tokens: what it read and wrote is estimated and counted.
    [(user, tokens)] = saved.tokens
    assert user == "ann" and tokens > 0


def test_a_turn_counts_against_the_instances_turns_while_it_streams(monkeypatch, saved):
    script(monkeypatch, text("Hello."))
    seen = []

    async def read():
        async for _ in turns.stream(TURN, [HumanMessage(content="Who am I?")]):
            seen.append(turns.running["turns"])

    asyncio.run(read())

    assert set(seen) == {1}
    assert turns.running["turns"] == 0


def test_a_new_message_is_refused_to_try_again_while_the_instance_is_full(monkeypatch):
    monkeypatch.setitem(turns.running, "turns", TURNS_AT_ONCE)
    counted = []

    async def check(*args):
        counted.append(args)

    monkeypatch.setattr(turns.limits, "check", check)
    user = User(uid="ann", email="ann@example.com", email_verified=True)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(turns.start(ChatRequest(message="Hello"), user, "user-token", "en"))

    assert refused.value.status_code == 503
    assert refused.value.detail == CHAT_FAILED
    assert refused.value.headers == {"Retry-After": str(TURNS_BUSY_RETRY_SECONDS)}
    assert counted == []
