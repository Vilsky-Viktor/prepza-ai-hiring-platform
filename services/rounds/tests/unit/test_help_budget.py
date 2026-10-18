import asyncio

import httpx
import openai
from fastapi import Request
from prepza_common.ai_constants import AI_USED, LIMIT_HIT

import app.routers.help as help_routes
from app.config.settings import settings
from app.constants.help import HELP_MAX_OUTPUT_TOKENS, HELP_SPEND_KEY
from app.integrations import llm
from app.schemas.help import HelpChatRequest
from tests.unit.test_help import CATALOG, fake_catalog

BODY = {"messages": [{"role": "user", "content": "How do I start?"}]}
USAGE = {"input_tokens": 1_000, "output_tokens": 234}


def answering(*parts, usage=None, error=None):
    """The model's answer: `parts`, its `usage`, then `error` raised when given."""

    async def stream(messages, used, run_id=None):
        for part in parts:
            yield part

        if usage:
            used["usage"] = usage

        if error:
            raise error

    return stream


def used(published) -> list[tuple]:
    """The AI calls recorded: action, model, tokens in and out, outcome, user."""
    return [
        (
            data["action"],
            data["model"],
            data["input_tokens"],
            data["output_tokens"],
            data["outcome"],
            data["user_id"],
        )
        for kind, data in published
        if kind == AI_USED
    ]


def test_a_finished_answer_is_recorded_and_counts_its_tokens(client, monkeypatch, redis, published):
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answering("Paste it.", usage=USAGE))

    response = client.post("/help/chat", json=BODY)

    assert response.status_code == 200
    assert used(published) == [("help_chat", settings.help_model, 1_000, 234, "ok", None)]
    # Counted against the day's budget after the answer.
    assert redis.counts[HELP_SPEND_KEY] == 1_234


def test_an_answer_that_fails_halfway_is_recorded_failed_with_its_tokens_estimated(
    client, monkeypatch, redis, published
):
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answering("x" * 40, error=TimeoutError()))

    response = client.post("/help/chat", json=BODY)

    assert '"error"' in response.text
    [(action, _, read, written, outcome, _)] = used(published)
    # The model read the guide and the question, and wrote 40 characters: about 10 tokens.
    assert (action, outcome) == ("help_chat", "failed")
    assert written == 10 and read > 1_000
    assert redis.counts[HELP_SPEND_KEY] == read + written
    # A timeout is no provider's limit.
    assert [kind for kind, _ in published if kind == LIMIT_HIT] == []


def test_openais_rate_limit_is_recorded_as_a_provider_hit(client, monkeypatch, published):
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com"))
    refused = openai.RateLimitError("Refused", response=response, body={"code": "rate_limit"})
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answering(error=refused))

    client.post("/help/chat", json=BODY)

    hits = [data for kind, data in published if kind == LIMIT_HIT]
    assert [(hit["limit"], hit["kind"], hit["what"]) for hit in hits] == [
        ("OPENAI_RATE_LIMIT", "provider:openai", "help_chat")
    ]
    assert [outcome for *_, outcome, _ in used(published)] == ["failed"]


def test_a_visitor_leaving_mid_answer_records_it_cut_and_counts_its_tokens(
    monkeypatch, redis, published
):
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answering("Paste ", "it.", usage=USAGE))
    scope = {"type": "http", "method": "POST", "path": "/help/chat", "headers": []}
    request = Request({**scope, "query_string": b"", "client": ("203.0.113.7", 1)})

    async def leave():
        response = await help_routes.help_chat(HelpChatRequest(**BODY), request, None)
        await anext(response.body_iterator)
        await response.body_iterator.aclose()

    asyncio.run(leave())

    assert [outcome for *_, outcome, _ in used(published)] == ["cut"]
    assert redis.counts[HELP_SPEND_KEY] > 0


def test_going_over_the_budget_with_an_answer_keeps_it_and_refuses_the_next(
    client, monkeypatch, redis
):
    redis.limits["HELP_TOKENS_PER_DAY"] = 1_000
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answering("Paste it.", usage=USAGE))

    kept = client.post("/help/chat", json=BODY)
    refused = client.post("/help/chat", json=BODY)

    assert '"done": true' in kept.text
    assert refused.status_code == 429


def test_an_answer_is_capped_and_reports_its_tokens(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm.get_help_llm.cache_clear()
    model = llm.get_help_llm()

    assert model.max_tokens == HELP_MAX_OUTPUT_TOKENS
    assert model.stream_usage is True
    llm.get_help_llm.cache_clear()
