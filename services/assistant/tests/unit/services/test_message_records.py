"""Each model call of an assistant turn is recorded as an AI call: its tokens, whose it was and
how it ended; OpenAI refusing it for its limits is recorded as a provider limit hit."""

import asyncio
import uuid

import httpx
import pytest
from langchain_core.messages import AIMessageChunk, HumanMessage
from openai import RateLimitError

from assistant.models.answers import Answer, Turn
from assistant.services.chat import ask
from tests.fake_model import FakeModel, text

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
TURN = Turn(uuid.uuid4(), "ann", COMPANY, "user-token", "en", frozenset({str(COMPANY)}))
PROMPT = [HumanMessage(content="x" * 400)]


class Failing:
    """Streams a few words, then raises `error`."""

    def __init__(self, error):
        self.error = error

    async def astream(self, messages, config=None):
        yield AIMessageChunk(content="Two candidates")
        raise self.error


def used(published) -> list[dict]:
    return [data for kind, data in published if kind == "ai.used"]


def test_a_finished_call_is_recorded_with_its_usage_and_whose_it_was(published):
    asyncio.run(ask(FakeModel(text("Two passed.")), PROMPT, TURN, Answer(), lambda event: None))

    [record] = used(published)
    assert (record["action"], record["input_tokens"], record["output_tokens"]) == (
        "assistant_message",
        10,
        5,
    )
    assert (record["company_id"], record["user_id"], record["subject_id"]) == (
        str(COMPANY),
        "ann",
        str(TURN.conversation_id),
    )
    assert record["outcome"] == "ok"
    assert record["cost_usd"] > 0


def test_a_failed_call_is_recorded_as_failed_with_its_tokens_estimated(published):
    with pytest.raises(TimeoutError):
        asyncio.run(ask(Failing(TimeoutError()), PROMPT, TURN, Answer(), lambda event: None))

    [record] = used(published)
    assert (record["outcome"], record["input_tokens"], record["output_tokens"]) == (
        "failed",
        100,
        4,
    )


def test_a_call_cut_short_is_recorded_as_cut(published):
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            ask(Failing(asyncio.CancelledError()), PROMPT, TURN, Answer(), lambda event: None)
        )

    [record] = used(published)
    assert (record["action"], record["outcome"]) == ("assistant_message", "cut")


@pytest.mark.parametrize(
    ("code", "limit"),
    [("rate_limit_exceeded", "OPENAI_RATE_LIMIT"), ("insufficient_quota", "OPENAI_QUOTA")],
)
def test_openai_refusing_for_its_limits_is_recorded_as_its_limit_hit(code, limit, published):
    request = httpx.Request("POST", "https://api.openai.com")
    error = RateLimitError(
        "over", response=httpx.Response(429, request=request), body={"code": code}
    )

    with pytest.raises(RateLimitError):
        asyncio.run(ask(Failing(error), PROMPT, TURN, Answer(), lambda event: None))

    hits = [data for kind, data in published if kind == "limit.hit"]
    assert [
        (hit["limit"], hit["kind"], hit["what"], hit["company_id"], hit["user_id"]) for hit in hits
    ] == [(limit, "provider:openai", "assistant_message", str(COMPANY), "ann")]
    assert used(published)[0]["outcome"] == "failed"
