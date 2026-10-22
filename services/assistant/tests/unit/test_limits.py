import asyncio

import pytest
from fake_redis import FakeRedis

from app.services import limits

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"


@pytest.fixture
def counted(monkeypatch):
    """The cap, counters and budgets each call reads, in order, with the limits by name."""
    made = []

    async def hit(redis, key, name, *, company_id=None, user_id=None):
        made.append(("hit", key, name))

    async def spend(redis, key, amount, name, *, company_id=None, user_id=None):
        made.append(("spend", key, amount, name))

    async def capped(redis, company_id=None, user_id=None):
        made.append(("cap", company_id, user_id))

    async def unpaid(redis, company_id):
        return False

    monkeypatch.setattr(limits, "hit", hit)
    monkeypatch.setattr(limits, "spend", spend)
    monkeypatch.setattr(limits, "refuse_if_capped", capped)
    monkeypatch.setattr(limits, "company_paid", unpaid)

    return made


def test_a_message_checks_the_cap_every_budget_then_counts_against_every_limit(counted):
    asyncio.run(limits.check(None, "ann", COMPANY))

    assert counted == [
        ("cap", COMPANY, "ann"),
        ("spend", "spend:assistant:user:ann", 0, "TOKENS_PER_USER_DAY"),
        ("spend", f"spend:assistant:company:{COMPANY}", 0, "TOKENS_PER_COMPANY_DAY"),
        ("spend", "spend:assistant:all", 0, "TOKENS_PER_DAY"),
        ("hit", "rate:assistant:hour:ann", "MESSAGES_PER_USER_HOUR"),
        ("hit", "rate:assistant:day:ann", "MESSAGES_PER_USER_DAY"),
        ("hit", f"rate:assistant:company:{COMPANY}", "MESSAGES_PER_COMPANY_DAY"),
        ("hit", "rate:assistant:all", "MESSAGES_PER_DAY"),
    ]


def test_a_company_that_paid_isnt_held_to_everyones_limits_or_the_cap(counted, monkeypatch):
    async def paid(redis, company_id):
        return True

    monkeypatch.setattr(limits, "company_paid", paid)
    asyncio.run(limits.check(None, "ann", COMPANY))

    assert not any(item[0] == "cap" or item[1].endswith(":all") for item in counted)
    assert ("hit", f"rate:assistant:company:{COMPANY}", "MESSAGES_PER_COMPANY_DAY") in counted


def test_whether_a_company_paid_is_asked_of_billing_once_in_a_while(monkeypatch):
    asked = []

    async def from_billing(company_id):
        asked.append(company_id)

        return True

    monkeypatch.setattr(limits.billing, "company_paid", from_billing)
    redis = FakeRedis()

    assert asyncio.run(limits.company_paid(redis, COMPANY)) is True
    assert asyncio.run(limits.company_paid(redis, COMPANY)) is True
    assert asyncio.run(limits.company_paid(redis, None)) is False
    assert asked == [COMPANY]


def test_without_a_company_only_the_users_and_everyones_count(counted):
    asyncio.run(limits.check(None, "ann", None))

    assert ("cap", None, "ann") in counted
    assert not any("company" in str(item[1]) for item in counted)


def test_a_turns_tokens_are_added_to_every_budget(monkeypatch):
    async def unpaid(redis, company_id):
        return False

    monkeypatch.setattr(limits, "company_paid", unpaid)
    redis = FakeRedis()
    asyncio.run(limits.record(redis, "ann", COMPANY, 1_234))

    assert redis.counts == {
        "spend:assistant:user:ann": 1_234,
        f"spend:assistant:company:{COMPANY}": 1_234,
        "spend:assistant:all": 1_234,
    }


def test_going_over_a_budget_or_redis_down_never_fails_the_turn(monkeypatch):
    class Down(FakeRedis):
        def pipeline(self, transaction=True):
            raise ConnectionError("Redis is down")

    async def unpaid(redis, company_id):
        return False

    monkeypatch.setattr(limits, "company_paid", unpaid)
    over = FakeRedis({"TOKENS_PER_USER_DAY": 10_000})
    over.counts["spend:assistant:user:ann"] = 10_000

    asyncio.run(limits.record(over, "ann", COMPANY, 5_000))
    asyncio.run(limits.record(Down(), "ann", COMPANY, 5_000))

    assert over.counts["spend:assistant:user:ann"] == 15_000


def test_a_voice_message_checks_the_cap_the_users_and_everyones_budgets_and_its_own_limit(
    counted,
):
    asyncio.run(limits.check_transcription(None, "ann", frozenset({COMPANY})))

    assert counted == [
        ("cap", None, "ann"),
        ("spend", "spend:assistant:user:ann", 0, "TOKENS_PER_USER_DAY"),
        ("spend", "spend:assistant:all", 0, "TOKENS_PER_DAY"),
        ("hit", "rate:assistant:transcribe:hour:ann", "TRANSCRIPTIONS_PER_USER_HOUR"),
    ]


def test_a_voice_message_of_someone_in_a_company_that_paid_isnt_capped(counted, monkeypatch):
    async def paid(redis, company_id):
        return str(company_id) == COMPANY

    monkeypatch.setattr(limits, "company_paid", paid)
    other = "1c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
    asyncio.run(limits.check_transcription(None, "ann", frozenset({other, COMPANY})))

    assert not any(item[0] == "cap" for item in counted)
