import asyncio

import httpx
import openai
from fastapi import Request
from testee_common.ai.ai_constants import AI_USED, LIMIT_HIT

from assistant.config import settings
from assistant.constants.help_chat import HELP_SPEND_KEY
from assistant.schemas.help_chat import HelpChatRequest
from assistant.services import help_answers
from assistant.services.turns import running
from tests.unit.help_setup import BODY, answering

USAGE = {"input_tokens": 1_000, "output_tokens": 234}


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


def test_a_finished_answer_is_recorded_and_counts_its_tokens(
    client, monkeypatch, help_redis, published
):
    monkeypatch.setattr(help_answers, "stream_reply", answering("Paste it.", usage=USAGE))

    response = client.post("/help/chat", json=BODY)

    assert response.status_code == 200
    assert used(published) == [("help_chat", settings.help_model, 1_000, 234, "ok", None)]
    # Counted against the day's budget after the answer.
    assert help_redis.counts[HELP_SPEND_KEY] == 1_234


def test_an_answer_that_fails_halfway_is_recorded_failed_with_its_tokens_estimated(
    client, monkeypatch, help_redis, published
):
    monkeypatch.setattr(help_answers, "stream_reply", answering("x" * 40, error=TimeoutError()))

    response = client.post("/help/chat", json=BODY)

    assert '"error"' in response.text
    [(action, _, read, written, outcome, _)] = used(published)
    # The model read the guide and the question, and wrote 40 characters: about 10 tokens.
    assert (action, outcome) == ("help_chat", "failed")
    assert written == 10 and read > 100
    assert help_redis.counts[HELP_SPEND_KEY] == read + written
    # A timeout is no provider's limit.
    assert [kind for kind, _ in published if kind == LIMIT_HIT] == []


def test_openais_rate_limit_is_recorded_as_a_provider_hit(
    client, monkeypatch, help_redis, published
):
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com"))
    refused = openai.RateLimitError("Refused", response=response, body={"code": "rate_limit"})
    monkeypatch.setattr(help_answers, "stream_reply", answering(error=refused))

    client.post("/help/chat", json=BODY)

    hits = [data for kind, data in published if kind == LIMIT_HIT]
    assert [(hit["limit"], hit["kind"], hit["what"]) for hit in hits] == [
        ("OPENAI_RATE_LIMIT", "provider:openai", "help_chat")
    ]
    assert [outcome for *_, outcome, _ in used(published)] == ["failed"]


def test_a_visitor_leaving_mid_answer_records_it_cut_and_counts_its_tokens(
    monkeypatch, help_redis, published
):
    monkeypatch.setattr(help_answers, "stream_reply", answering("Paste ", "it.", usage=USAGE))
    scope = {"type": "http", "method": "POST", "path": "/help/chat", "headers": []}
    request = Request({**scope, "query_string": b"", "client": ("203.0.113.7", 1)})

    async def leave():
        events = await help_answers.start(HelpChatRequest(**BODY), request, None, None, "en")
        await anext(events)
        await events.aclose()

    asyncio.run(leave())

    assert [outcome for *_, outcome, _ in used(published)] == ["cut"]
    assert help_redis.counts[HELP_SPEND_KEY] > 0
    # It no longer counts among the instance's streaming turns.
    assert running["turns"] == 0


def test_going_over_the_budget_with_an_answer_keeps_it_and_refuses_the_next(
    client, monkeypatch, help_redis
):
    help_redis.limits["HELP_TOKENS_PER_DAY"] = 1_000
    monkeypatch.setattr(help_answers, "stream_reply", answering("Paste it.", usage=USAGE))

    kept = client.post("/help/chat", json=BODY)
    refused = client.post("/help/chat", json=BODY)

    assert '"done": true' in kept.text
    assert refused.status_code == 429
