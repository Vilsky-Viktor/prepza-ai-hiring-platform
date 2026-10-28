import asyncio

import openai
import pytest
from fake_redis import FakeRedis
from prepza_common.ai.ai_constants import AI_USED, LIMIT_HIT

from generation.constants.actions import KEY_CHECK_BATCH
from generation.integrations import openai_batch
from generation.services import batch_usage, key_check_batches
from tests.unit.fake_ai import MODEL, refused
from tests.unit.services.test_key_check_batches import KEPT, FakeStore, library_with


def test_a_finished_batchs_usage_is_recorded_once_at_batch_price(published, monkeypatch):
    store = FakeStore({KEPT: "batch-1"})
    store.install(monkeypatch)
    library_with(monkeypatch, {KEPT})

    async def status(batch_id):
        return "completed", "file-1"

    async def results(file_id):
        reply = '{"correct_indexes": [1]}'

        return {str(KEPT): reply}, [(str(KEPT), MODEL, {"input_tokens": 1_000_000})]

    async def applied(*args):
        pass

    traced = []
    redis = FakeRedis()
    monkeypatch.setattr(batch_usage.tracing, "traced_call", lambda *a: traced.append(a))
    monkeypatch.setattr(batch_usage, "get_redis", lambda: redis)
    monkeypatch.setattr(openai_batch, "status", status)
    monkeypatch.setattr(openai_batch, "results", results)
    monkeypatch.setattr(key_check_batches, "apply_key_check", applied)

    asyncio.run(key_check_batches.collect_finished())
    # A run that stopped halfway reads the same batch again.
    store.rows[KEPT] = "batch-1"
    asyncio.run(key_check_batches.collect_finished())

    [data] = [data for kind, data in published if kind == AI_USED]
    assert (data["action"], data["model"], data["input_tokens"], data["subject_id"]) == (
        KEY_CHECK_BATCH,
        MODEL,
        1_000_000,
        str(KEPT),
    )
    # A million tokens in at $2, at half price.
    assert data["cost_usd"] == pytest.approx(1.0)
    # Traced once, to the question's verify trace, with its cost and reply.
    [(name, tags, seed, model, _usage, cost, output)] = traced
    assert (name, tags, seed, model) == (
        KEY_CHECK_BATCH,
        [KEY_CHECK_BATCH, str(KEPT)],
        f"question_verify:{KEPT}",
        MODEL,
    )
    assert (cost, output) == (pytest.approx(1.0), '{"correct_indexes": [1]}')


def test_openai_refusing_a_batch_is_recorded_as_its_limit_hit(published, monkeypatch):
    store = FakeStore({KEPT: None})
    store.install(monkeypatch)
    library_with(monkeypatch, {KEPT})

    async def submit(requests):
        raise refused("rate_limit_exceeded")

    monkeypatch.setattr(openai_batch, "submit", submit)

    with pytest.raises(openai.RateLimitError):
        asyncio.run(key_check_batches.submit_pending())

    [hit] = [data for kind, data in published if kind == LIMIT_HIT]
    assert (hit["limit"], hit["kind"], hit["what"]) == (
        "OPENAI_RATE_LIMIT",
        "provider:openai",
        KEY_CHECK_BATCH,
    )
    # Still waiting, for the next run.
    assert store.rows == {KEPT: None}
