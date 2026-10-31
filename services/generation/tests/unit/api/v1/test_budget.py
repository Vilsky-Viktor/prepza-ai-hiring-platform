import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from testee_common.ai.ai_constants import LIMIT_HIT
from testee_common.http.http import bearer
from testee_common.limits.limit_list import LIMITS

from generation.api.v1 import internal
from generation.constants.generation import BUDGET_KEY, GENERATIONS_PAUSED
from generation.core.security import service_token
from generation.services import budget

COMPANY_ID = uuid.uuid4()


def test_generations_past_the_daily_limits_edited_value_wait_until_tomorrow(redis, published):
    redis.limits["DAILY_GENERATION_LIMIT"] = "2"

    asyncio.run(budget.use_daily_budget())
    asyncio.run(budget.use_daily_budget())

    with pytest.raises(HTTPException) as paused:
        asyncio.run(budget.use_daily_budget(company_id=COMPANY_ID, user_id="bob"))

    assert paused.value.status_code == 503
    assert 0 < int(paused.value.headers["Retry-After"]) <= 24 * 60 * 60
    assert paused.value.detail == GENERATIONS_PAUSED
    [key] = redis.counts
    assert key.startswith(f"{BUDGET_KEY}:")
    [(kind, hit)] = published
    assert kind == LIMIT_HIT
    assert (hit["limit"], hit["company_id"], hit["user_id"]) == (
        "DAILY_GENERATION_LIMIT",
        str(COMPANY_ID),
        "bob",
    )


def test_without_an_edited_value_the_default_holds(redis):
    default = LIMITS["DAILY_GENERATION_LIMIT"].default
    redis.counts[budget.day_key(BUDGET_KEY)] = default - 1

    asyncio.run(budget.use_daily_budget())

    with pytest.raises(HTTPException) as paused:
        asyncio.run(budget.use_daily_budget())

    assert paused.value.detail == GENERATIONS_PAUSED


def test_a_company_that_paid_isnt_held_to_the_limit_free_accounts_used_up(redis):
    redis.limits["DAILY_GENERATION_LIMIT"] = "1"
    asyncio.run(budget.use_daily_budget())

    with pytest.raises(HTTPException):
        asyncio.run(budget.use_daily_budget(paid=False))

    asyncio.run(budget.use_daily_budget(paid=True))

    # A paying company's generations don't count either, so they never use it up.
    assert list(redis.counts.values()) == [2]


@pytest.mark.parametrize("paid", [False, True])
def test_a_regenerated_question_counts_toward_the_limit_unless_the_company_paid(
    client, monkeypatch, paid
):
    set_id = uuid.uuid4()
    counted = []

    async def context(question_id):
        return SimpleNamespace(set_id=set_id, kind="interview", owner_id=str(COMPANY_ID))

    async def daily(paid=False, **who):
        counted.append(paid)

    async def regenerated(question_id, found):
        return {"id": str(question_id), "text": "New question?", "options": []}

    monkeypatch.setattr(internal.library, "get_question_context", context)
    monkeypatch.setattr(internal, "use_daily_budget", daily)
    monkeypatch.setattr(internal, "regenerate", regenerated)

    client.post(
        f"/internal/questions/{uuid.uuid4()}/regenerate",
        json={"user_id": "bob", "set_id": str(set_id), "paid": paid},
        headers=bearer(service_token("generation")),
    )

    assert counted == [paid]
