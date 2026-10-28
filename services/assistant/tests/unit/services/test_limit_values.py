"""Each limit refuses at its value as edited in the admin zone (the limits hash), and at its
default otherwise; a refusal is recorded. The unpaid daily AI spend cap holds only unpaid
companies and people without one."""

import asyncio
from datetime import UTC, datetime

import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException

from assistant.services import limits

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
PAID = "1c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
RATE_LIMITED = "Too many requests. Try again later."
AI_PAUSED_TODAY = (
    "AI features are paused for today. They're back tomorrow, or right away for companies that "
    "have topped up."
)


@pytest.fixture(autouse=True)
def paid_companies(monkeypatch):
    """Only PAID ever topped up."""

    async def paid(redis, company_id):
        return str(company_id) == PAID

    monkeypatch.setattr(limits, "company_paid", paid)


def refused(redis, user_id="ann", company_id=COMPANY) -> HTTPException:
    with pytest.raises(HTTPException) as error:
        asyncio.run(limits.check(redis, user_id, company_id))

    return error.value


def hits(published) -> list[tuple]:
    return [
        (data["limit"], data["user_id"], data["company_id"])
        for kind, data in published
        if kind == "limit.hit"
    ]


@pytest.mark.parametrize(
    ("name", "key", "default"),
    [
        ("MESSAGES_PER_USER_HOUR", "rate:assistant:hour:ann", 30),
        ("MESSAGES_PER_USER_DAY", "rate:assistant:day:ann", 200),
        ("MESSAGES_PER_COMPANY_DAY", f"rate:assistant:company:{COMPANY}", 1_000),
        ("MESSAGES_PER_DAY", "rate:assistant:all", 20_000),
    ],
)
def test_a_message_limit_refuses_at_its_default(name, key, default, published):
    redis = FakeRedis()
    redis.counts[key] = default - 1
    asyncio.run(limits.check(redis, "ann", COMPANY))

    error = refused(redis)

    assert (error.status_code, error.detail) == (429, RATE_LIMITED)
    assert hits(published) == [(name, "ann", COMPANY)]


def test_a_message_limit_refuses_at_its_edited_value(published):
    redis = FakeRedis({"MESSAGES_PER_USER_HOUR": 2})

    for _ in range(2):
        asyncio.run(limits.check(redis, "ann", COMPANY))

    error = refused(redis)

    assert (error.status_code, error.detail) == (429, RATE_LIMITED)
    assert hits(published) == [("MESSAGES_PER_USER_HOUR", "ann", COMPANY)]


def test_the_company_limit_counts_its_members_together_at_its_edited_value(published):
    redis = FakeRedis({"MESSAGES_PER_COMPANY_DAY": 2})
    asyncio.run(limits.check(redis, "ann", COMPANY))
    asyncio.run(limits.check(redis, "bob", COMPANY))

    assert refused(redis, "cid").status_code == 429
    assert hits(published) == [("MESSAGES_PER_COMPANY_DAY", "cid", COMPANY)]
    # Another company's members go on.
    asyncio.run(limits.check(redis, "dan", None))


def test_a_token_budget_refuses_once_spent_at_its_edited_value(published):
    redis = FakeRedis({"TOKENS_PER_USER_DAY": 10_000})
    asyncio.run(limits.record(redis, "ann", COMPANY, 10_000))
    asyncio.run(limits.check(redis, "ann", COMPANY))
    asyncio.run(limits.record(redis, "ann", COMPANY, 1))

    assert refused(redis).status_code == 429
    assert hits(published) == [("TOKENS_PER_USER_DAY", "ann", COMPANY)]


def test_a_token_budget_refuses_once_spent_at_its_default(published):
    redis = FakeRedis()
    asyncio.run(limits.record(redis, "ann", COMPANY, 2_000_000))
    asyncio.run(limits.check(redis, "ann", COMPANY))
    asyncio.run(limits.record(redis, "ann", COMPANY, 1))

    assert refused(redis).status_code == 429
    assert hits(published) == [("TOKENS_PER_USER_DAY", "ann", COMPANY)]


def test_the_companys_token_budget_refuses_its_members_at_its_default(published):
    redis = FakeRedis()
    redis.counts[f"spend:assistant:company:{COMPANY}"] = 6_000_000
    asyncio.run(limits.check(redis, "bob", COMPANY))
    redis.counts[f"spend:assistant:company:{COMPANY}"] = 6_000_001

    assert refused(redis, "bob").status_code == 429
    assert hits(published) == [("TOKENS_PER_COMPANY_DAY", "bob", COMPANY)]


def test_a_voice_message_limit_refuses_at_its_edited_value(published):
    redis = FakeRedis({"TRANSCRIPTIONS_PER_USER_HOUR": 1})
    asyncio.run(limits.check_transcription(redis, "ann", frozenset({COMPANY})))

    with pytest.raises(HTTPException) as error:
        asyncio.run(limits.check_transcription(redis, "ann", frozenset({COMPANY})))

    assert (error.value.status_code, error.value.detail) == (429, RATE_LIMITED)
    assert hits(published) == [("TRANSCRIPTIONS_PER_USER_HOUR", "ann", None)]


def spent_today(redis, usd: float) -> None:
    redis.counts[f"spend:ai:unpaid:{datetime.now(UTC).date().isoformat()}"] = round(usd * 1e6)


@pytest.mark.parametrize("company_id", [COMPANY, None])
def test_an_unpaid_message_is_refused_once_the_spend_cap_is_reached(company_id, published):
    redis = FakeRedis()
    spent_today(redis, 14.99)
    asyncio.run(limits.check(redis, "ann", company_id))
    spent_today(redis, 15.0)

    error = refused(redis, company_id=company_id)

    assert (error.status_code, error.detail) == (503, AI_PAUSED_TODAY)
    assert hits(published) == [("AI_SPEND_UNPAID_DAY", "ann", company_id)]


def test_the_spend_cap_refuses_at_its_edited_value_and_a_paid_companys_message_goes_on(
    published,
):
    redis = FakeRedis({"AI_SPEND_UNPAID_DAY": 2.0})
    spent_today(redis, 2.0)

    assert refused(redis).status_code == 503
    asyncio.run(limits.check(redis, "ann", PAID))
    assert hits(published) == [("AI_SPEND_UNPAID_DAY", "ann", COMPANY)]


def test_a_voice_message_is_capped_unless_one_of_the_users_companies_paid(published):
    redis = FakeRedis()
    spent_today(redis, 15.0)

    with pytest.raises(HTTPException) as error:
        asyncio.run(limits.check_transcription(redis, "ann", frozenset({COMPANY})))

    assert (error.value.status_code, error.value.detail) == (503, AI_PAUSED_TODAY)
    asyncio.run(limits.check_transcription(redis, "ann", frozenset({COMPANY, PAID})))


def test_the_shared_budgets_are_read_from_redis_with_their_current_limits():
    redis = FakeRedis({"MESSAGES_PER_DAY": 500})
    redis.counts.update({"spend:assistant:all": 1_500_000, "rate:assistant:all": 125})

    found = asyncio.run(limits.shared_budgets(redis))

    assert [(b.name, b.used, b.limit, b.unit) for b in found] == [
        ("TOKENS_PER_DAY", 1_500_000, 200_000_000, "tokens"),
        ("MESSAGES_PER_DAY", 125, 500, "calls"),
        # The help chat's, at their defaults, nothing used yet today.
        ("HELP_TOKENS_PER_DAY", 0, 50_000_000, "tokens"),
        ("HELP_DAILY_LIMIT", 0, 5_000, "calls"),
    ]
