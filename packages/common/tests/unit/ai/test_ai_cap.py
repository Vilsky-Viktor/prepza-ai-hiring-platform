import asyncio
import logging
from datetime import UTC, datetime

import pytest
from fake_redis import DownRedis, FakeRedis
from fastapi import HTTPException
from prepza_common.ai import ai_cap
from prepza_common.ai.ai_cap import CAP, add_unpaid, refuse_if_capped, spent_today
from prepza_common.ai.ai_constants import AI_PAUSED_TODAY, LIMIT_HIT
from prepza_common.i18n.translations import TRANSLATIONS
from prepza_common.redis import memory_cache


def on(monkeypatch, moment: datetime):
    """Makes it `moment` (UTC) for the cap's daily counter."""

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment

    monkeypatch.setattr(ai_cap, "datetime", Clock)


def capped(redis, **who) -> bool:
    try:
        asyncio.run(refuse_if_capped(redis, **who))
    except HTTPException as error:
        assert (error.status_code, error.detail) == (503, AI_PAUSED_TODAY)
        # Until the next UTC day, at most a day away.
        assert 0 < int(error.headers["Retry-After"]) <= 24 * 60 * 60

        return True

    return False


def test_unpaid_calls_are_refused_once_todays_spend_reaches_the_cap(published):
    redis = FakeRedis({CAP: 10})
    asyncio.run(add_unpaid(redis, 9.99))

    assert not capped(redis, company_id="c1", user_id="u1")

    asyncio.run(add_unpaid(redis, 0.01))

    assert asyncio.run(spent_today(redis)) == pytest.approx(10.0)
    assert capped(redis, company_id="c1", user_id="u1")
    assert [(kind, data["limit"], data["company_id"]) for kind, data in published] == [
        (LIMIT_HIT, CAP, "c1")
    ]


def test_the_default_cap_holds_until_edited(monkeypatch, published):
    redis = FakeRedis()
    asyncio.run(add_unpaid(redis, 14.99))

    assert not capped(redis)

    redis.limits[CAP] = "14"
    monkeypatch.setattr(memory_cache, "_entries", {})

    assert capped(redis)


def test_the_counter_starts_again_at_midnight_utc(monkeypatch, published):
    redis = FakeRedis({CAP: 5})
    on(monkeypatch, datetime(2026, 10, 16, 23, 59, tzinfo=UTC))
    asyncio.run(add_unpaid(redis, 5))

    assert capped(redis)

    on(monkeypatch, datetime(2026, 10, 17, 0, 0, tzinfo=UTC))

    assert not capped(redis)
    # Kept a while past its day, so late calls are still read.
    assert redis.expiries["spend:ai:unpaid:2026-10-16"] >= 24 * 60 * 60


def test_with_redis_down_nothing_is_refused():
    assert not capped(DownRedis())


def test_reaching_80_percent_and_the_cap_each_alert_once(caplog):
    redis = FakeRedis({CAP: 10})

    with caplog.at_level(logging.WARNING, logger=ai_cap.__name__):
        for _ in range(12):
            asyncio.run(add_unpaid(redis, 1))

    alerts = [(record.levelname, record.getMessage()) for record in caplog.records]
    assert alerts == [
        ("WARNING", "Unpaid AI spend near the daily cap: $8.00"),
        ("ERROR", "Unpaid AI spend reached the daily cap: $10.00"),
    ]


def test_the_refusal_has_translations():
    for language in TRANSLATIONS.values():
        assert AI_PAUSED_TODAY in language
