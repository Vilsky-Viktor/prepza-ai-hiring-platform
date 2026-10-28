import asyncio
import uuid

import openai
import pytest
from prepza_common.ai.ai_constants import AI_USED, LIMIT_HIT
from prepza_common.ai.llm import estimated_tokens

from generation.config import settings
from generation.constants.actions import EMBEDDINGS, INTERVIEW_GENERATION
from generation.integrations import llm, usage
from tests.unit.fake_ai import HANG, MODEL, Chat, refused, reply

COMPANY_ID = uuid.uuid4()
SUBJECT_ID = uuid.uuid4()
WHO = {"company_id": COMPANY_ID, "user_id": "bob", "subject_id": SUBJECT_ID}


def used(events):
    return [data for kind, data in events if kind == AI_USED]


def hits(events):
    return [data for kind, data in events if kind == LIMIT_HIT]


def test_a_run_records_one_call_per_model_with_its_summed_usage(events):
    chat = Chat(
        replies=[reply(300_000, 60_000), reply(200_000, 40_000), reply(10, 2, "gpt-6-luna")]
    )

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, **WHO):
            for _ in range(3):
                await chat.ainvoke("Write the questions")

    asyncio.run(run())

    by_model = {data["model"]: data for data in used(events)}
    assert set(by_model) == {MODEL, "gpt-6-luna"}
    data = by_model[MODEL]
    assert (data["input_tokens"], data["output_tokens"]) == (500_000, 100_000)
    # 500,000 in at $2 and 100,000 out at $10 a million.
    assert data["cost_usd"] == pytest.approx(2.0)
    assert (data["action"], data["outcome"]) == (INTERVIEW_GENERATION, "ok")
    assert (data["company_id"], data["user_id"], data["subject_id"]) == (
        str(COMPANY_ID),
        "bob",
        str(SUBJECT_ID),
    )


def test_a_run_cut_short_records_its_unanswered_call_estimated(events):
    chat = Chat(replies=[reply(100, 10), HANG])
    prompt = "Write the questions"

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, **WHO):
            await chat.ainvoke(prompt)
            await chat.ainvoke(prompt)

    async def cancelled():
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(run(), 0.05)

    asyncio.run(cancelled())

    answered, unanswered = used(events)
    assert (answered["input_tokens"], answered["outcome"]) == (100, "cut")
    assert (unanswered["input_tokens"], unanswered["output_tokens"]) == (
        estimated_tokens(prompt),
        0,
    )
    assert (unanswered["model"], unanswered["outcome"]) == (MODEL, "cut")


def test_a_run_that_fails_records_what_it_used_as_failed(events):
    chat = Chat(replies=[reply(100, 10)])

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, **WHO):
            await chat.ainvoke("Write the questions")

            raise ValueError("The library is down")

    with pytest.raises(ValueError):
        asyncio.run(run())

    [data] = used(events)
    assert (data["input_tokens"], data["outcome"]) == (100, "failed")


@pytest.mark.parametrize(
    "code, limit",
    [("insufficient_quota", "OPENAI_QUOTA"), ("rate_limit_exceeded", "OPENAI_RATE_LIMIT")],
)
def test_openai_refusing_a_call_is_recorded_as_its_limit_hit(events, code, limit):
    chat = Chat(replies=[refused(code)])

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, **WHO):
            await chat.ainvoke("Write the questions")

    with pytest.raises(openai.RateLimitError):
        asyncio.run(run())

    [hit] = hits(events)
    assert (hit["limit"], hit["kind"], hit["what"]) == (
        limit,
        "provider:openai",
        INTERVIEW_GENERATION,
    )
    assert (hit["company_id"], hit["user_id"]) == (str(COMPANY_ID), "bob")
    # The call it refused is recorded as failed, its input estimated.
    [data] = used(events)
    assert data["outcome"] == "failed"


class Embeddings:
    def __init__(self, error=None):
        self.error = error

    async def aembed_documents(self, texts):
        if self.error:
            raise self.error

        return [[1.0] for _ in texts]


def test_embeddings_are_recorded_for_the_runs_company_with_their_input_estimated(
    events, monkeypatch
):
    monkeypatch.setattr(llm, "get_embeddings", lambda: Embeddings())
    texts = ["Python: asyncio", "SQL: joins"]

    async def run():
        async with usage.ai_run(INTERVIEW_GENERATION, **WHO):
            return await usage.embed(texts)

    assert asyncio.run(run()) == [[1.0], [1.0]]

    [data] = used(events)
    assert (data["action"], data["model"], data["outcome"]) == (
        EMBEDDINGS,
        settings.embedding_model,
        "ok",
    )
    assert data["input_tokens"] == sum(estimated_tokens(text) for text in texts)
    assert (data["company_id"], data["user_id"]) == (str(COMPANY_ID), "bob")


def test_refused_embeddings_are_a_provider_hit_and_a_failed_call(events, monkeypatch):
    monkeypatch.setattr(llm, "get_embeddings", lambda: Embeddings(refused("insufficient_quota")))

    with pytest.raises(openai.RateLimitError):
        asyncio.run(usage.embed(["Python"]))

    [hit] = hits(events)
    assert (hit["limit"], hit["what"]) == ("OPENAI_QUOTA", EMBEDDINGS)
    [data] = used(events)
    assert (data["action"], data["outcome"], data["company_id"]) == (EMBEDDINGS, "failed", None)
