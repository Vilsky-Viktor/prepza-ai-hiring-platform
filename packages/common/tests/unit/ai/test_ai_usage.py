import asyncio
from unittest import mock

import httpx
import openai
import pytest
from testee_common.ai import ai_usage
from testee_common.ai.ai_constants import AI_USED, LIMIT_HIT, Outcome
from testee_common.events import pubsub


def refused(code: str) -> openai.RateLimitError:
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com"))

    return openai.RateLimitError("Refused", response=response, body={"code": code})


def test_a_call_is_recorded_with_its_tokens_and_cost(published):
    usage = {
        "input_tokens": 2_000,
        "input_token_details": {"cache_read": 1_000},
        "output_tokens": 500,
    }
    asyncio.run(
        ai_usage.record(
            "assistant_message",
            "gpt-6.1-sol",
            usage,
            company_id="c1",
            user_id="u1",
            subject_id="m1",
        )
    )

    assert published == [
        (
            AI_USED,
            {
                "action": "assistant_message",
                "service": "assistant",
                "model": "gpt-6.1-sol",
                "input_tokens": 2_000,
                "cached_input_tokens": 1_000,
                "output_tokens": 500,
                "audio_seconds": 0.0,
                # 1,000 fresh at $2, 1,000 cached at $0.20 and 500 out at $10 a million.
                "cost_usd": pytest.approx(0.0072),
                "company_id": "c1",
                "user_id": "u1",
                "subject_id": "m1",
                "outcome": "ok",
            },
        )
    ]


def test_a_batch_call_is_recorded_at_half_price(published):
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}
    asyncio.run(ai_usage.record("key_check_batch", "gpt-6.1-sol", usage, batch=True))

    assert published[0][1]["cost_usd"] == pytest.approx(1.0)


def test_transcription_is_recorded_by_its_seconds(published):
    asyncio.run(ai_usage.record("transcription", "gpt-transcribe", audio_seconds=60, user_id="u1"))

    data = published[0][1]
    assert (data["audio_seconds"], data["cost_usd"]) == (60, pytest.approx(0.0045))
    assert (data["input_tokens"], data["output_tokens"]) == (0, 0)


def test_a_failed_call_of_a_model_without_a_price_is_recorded_at_no_cost(published):
    asyncio.run(
        ai_usage.record("help_chat", "unknown-model", {"input_tokens": 10}, outcome=Outcome.FAILED)
    )

    data = published[0][1]
    assert (data["cost_usd"], data["outcome"], data["service"]) == (0.0, "failed", "assistant")


def test_a_publish_that_fails_never_fails_the_call(monkeypatch):
    monkeypatch.setattr(pubsub, "publish_batch", mock.AsyncMock(side_effect=ConnectionError))

    asyncio.run(ai_usage.record("help_chat", "gpt-6-luna", {"input_tokens": 10}))


def test_openais_rate_limit_and_quota_are_recorded_as_its_limits(published):
    asyncio.run(ai_usage.provider_refused(refused("rate_limit_exceeded"), "help_chat"))
    asyncio.run(ai_usage.provider_refused(refused("insufficient_quota"), "assistant_message"))

    assert [(kind, data["limit"], data["kind"], data["what"]) for kind, data in published] == [
        (LIMIT_HIT, "OPENAI_RATE_LIMIT", "provider:openai", "help_chat"),
        (LIMIT_HIT, "OPENAI_QUOTA", "provider:openai", "assistant_message"),
    ]


def test_other_errors_are_no_limit_hits(published):
    asyncio.run(ai_usage.provider_refused(TimeoutError(), "help_chat"))

    assert published == []
