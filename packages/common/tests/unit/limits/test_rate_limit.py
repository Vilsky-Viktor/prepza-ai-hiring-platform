import asyncio
from datetime import UTC, datetime

import pytest
from fake_redis import DownRedis, FakeRedis
from fastapi import HTTPException
from prepza_common.ai.ai_constants import LIMIT_HIT
from prepza_common.limits import rate_limit
from prepza_common.limits.limit_list import LIMITS
from prepza_common.limits.rate_limit import (
    add_spent,
    hit,
    hit_emails,
    hit_or_skip,
    recipient_key,
    spend,
    until_tomorrow,
)

# A limit counted an hour, and one in tokens a day.
HOURLY = "PRACTICE_ROUNDS_PER_HOUR"
TOKENS = "TOKENS_PER_DAY"


def statuses(calls):
    """200 for each call that passed, 429 for each one the limit refused."""
    codes = []

    for call in calls:
        try:
            asyncio.run(call())
            codes.append(200)
        except HTTPException as error:
            codes.append(error.status_code)

    return codes


def test_hit_refuses_past_the_limits_edited_value(published):
    redis = FakeRedis({HOURLY: 2})

    assert statuses([lambda: hit(redis, "key", HOURLY)] * 3) == [200, 200, 429]
    # Counted over the limit's window, an hour.
    assert redis.counts == {"key": 3}
    assert redis.expiries == {"key": 3600}


def test_without_an_edited_value_the_default_holds(published):
    redis = FakeRedis()
    default = LIMITS[HOURLY].default

    codes = statuses([lambda: hit(redis, "key", HOURLY)] * (default + 1))

    assert codes == [200] * default + [429]


def test_a_refusal_says_the_current_value_and_is_recorded(published):
    redis = FakeRedis({HOURLY: 1})
    asyncio.run(hit(redis, "key", HOURLY, "At most {limit} an hour.", user_id="u1"))

    with pytest.raises(HTTPException) as refused:
        asyncio.run(hit(redis, "key", HOURLY, "At most {limit} an hour.", user_id="u1"))

    assert refused.value.detail == "At most 1 an hour."
    assert published == [
        (
            LIMIT_HIT,
            {
                "limit": HOURLY,
                "kind": "ours",
                "scope": "user",
                "company_id": None,
                "user_id": "u1",
                "what": None,
            },
        )
    ]


def test_a_refusal_says_when_to_try_again(published):
    redis = FakeRedis({HOURLY: 1})
    asyncio.run(hit(redis, "key", HOURLY))
    # 20 minutes left in the window.
    redis.expiries["key"] = 1200

    with pytest.raises(HTTPException) as refused:
        asyncio.run(hit(redis, "key", HOURLY))

    assert refused.value.headers == {"Retry-After": "1200"}


def test_a_spent_budget_says_when_to_try_again(published):
    redis = FakeRedis({TOKENS: 10})

    with pytest.raises(HTTPException) as refused:
        asyncio.run(spend(redis, "key", 11, TOKENS))

    assert refused.value.headers == {"Retry-After": str(LIMITS[TOKENS].window)}


@pytest.mark.parametrize("value", [-1, 0])
def test_non_positive_limits_never_refuse(value, published):
    redis = FakeRedis({HOURLY: value})

    assert statuses([lambda: hit(redis, "key", HOURLY)] * 3) == [200, 200, 200]
    assert redis.counts == {}


def test_emails_are_limited_per_recipient(published):
    redis = FakeRedis({"EMAIL_RECIPIENT_DAILY_LIMIT": 3})

    def invite(recipient):
        return lambda: hit_emails(redis, "ann", recipient)

    assert statuses([invite("set-1:bob@example.com")] * 4) == [200, 200, 200, 429]
    # Another address, or the same one for something else, has its own count.
    assert statuses([invite("set-1:carol@example.com"), invite("set-2:bob@example.com")]) == [
        200,
        200,
    ]


@pytest.mark.parametrize(
    ("address", "key"),
    [
        ("Bob@Example.com", "bob@example.com"),
        ("bob+jobs@example.com", "bob@example.com"),
        (" Bob+a+b@Example.com ", "bob@example.com"),
        ("+tag@example.com", "@example.com"),
        ("not-an-address", "not-an-address"),
    ],
)
def test_a_recipients_key_is_its_inbox(address, key):
    assert recipient_key(address) == key


def test_tagged_addresses_share_their_inboxs_count(published):
    redis = FakeRedis({"EMAIL_RECIPIENT_DAILY_LIMIT": 2})
    calls = [
        lambda tag=tag: hit_emails(redis, "ann", f"set-1:{recipient_key(f'bob+{tag}@example.com')}")
        for tag in ("a", "b", "c")
    ]

    assert statuses(calls) == [200, 200, 429]


def test_an_address_over_its_limit_doesnt_use_up_the_senders_counts(published):
    redis = FakeRedis({"EMAIL_RECIPIENT_DAILY_LIMIT": 1})
    calls = [lambda: hit_emails(redis, "ann", "set-1:bob@example.com")] * 3

    assert statuses(calls) == [200, 429, 429]
    # Only the one email sent counts against Ann's hour and day.
    assert redis.counts["rate:emails:hour:ann"] == 1


def test_emails_are_limited_per_sender_across_recipients(published):
    redis = FakeRedis({"EMAIL_HOURLY_LIMIT": 2})
    calls = [lambda i=i: hit_emails(redis, "ann", f"set-1:{i}@example.com") for i in range(3)]

    assert statuses(calls) == [200, 200, 429]


def test_spend_refuses_once_the_total_is_over_the_limit(published):
    redis = FakeRedis({TOKENS: 100})
    calls = [lambda amount=amount: spend(redis, "key", amount, TOKENS) for amount in (60, 40, 1)]

    assert statuses(calls) == [200, 200, 429]
    assert redis.counts == {"key": 101}


def test_spending_nothing_only_checks_the_budget(published):
    redis = FakeRedis({TOKENS: 20})

    def check():
        return spend(redis, "key", 0, TOKENS)

    assert statuses([check, lambda: spend(redis, "key", 25, TOKENS), check]) == [200, 429, 429]
    assert redis.counts == {"key": 25}


@pytest.mark.parametrize("value", [-1, 0])
def test_spend_with_no_limit_counts_nothing(value, published):
    redis = FakeRedis({TOKENS: value})

    assert statuses([lambda: spend(redis, "key", 1_000, TOKENS)] * 2) == [200, 200]
    assert redis.counts == {}


def test_with_redis_down_a_use_goes_uncounted():
    # No exception: the request goes through.
    asyncio.run(hit_or_skip(DownRedis(), "rate:x:u1", HOURLY))


def test_over_a_limit_that_skips_on_failure_is_still_refused(published):
    redis = FakeRedis({HOURLY: 1})
    asyncio.run(hit_or_skip(redis, "rate:x:u1", HOURLY))

    with pytest.raises(HTTPException) as refused:
        asyncio.run(hit_or_skip(redis, "rate:x:u1", HOURLY))

    assert refused.value.status_code == 429


def test_adding_what_a_request_spent_goes_over_without_refusing_it(published):
    redis = FakeRedis({TOKENS: 100})
    asyncio.run(add_spent(redis, "spend:x:all", 500, TOKENS))

    assert redis.counts == {"spend:x:all": 500}
    # The next request is the one refused.
    assert statuses([lambda: spend(redis, "spend:x:all", 0, TOKENS)]) == [429]


def test_adding_what_a_request_spent_never_fails_it_with_redis_down():
    asyncio.run(rate_limit.add_spent(DownRedis(), "spend:x:all", 500, TOKENS))


def test_a_daily_cap_says_the_seconds_until_the_next_utc_day():
    evening = datetime(2026, 10, 20, 23, 59, 30, tzinfo=UTC)

    assert until_tomorrow(evening) == {"Retry-After": "30"}
