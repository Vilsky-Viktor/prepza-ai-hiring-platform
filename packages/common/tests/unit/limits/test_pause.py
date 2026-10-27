import asyncio

import pytest
from fake_redis import DownRedis, FakeRedis
from fastapi import HTTPException
from prepza_common.ai.ai_constants import LIMIT_HIT
from prepza_common.config.constants import PAUSE_KEY, PAUSED
from prepza_common.i18n.translations import TRANSLATIONS
from prepza_common.limits.limit_list import PAUSED_LIMIT
from prepza_common.limits.pause import is_paused, refuse_if_paused, set_paused


def test_the_switch_turns_on_and_off_and_remembers_who():
    redis = FakeRedis()

    asyncio.run(set_paused(redis, True, "ann"))

    assert redis.counts == {PAUSE_KEY: "ann"}
    assert asyncio.run(is_paused(redis))

    asyncio.run(set_paused(redis, False, "ann"))

    assert not asyncio.run(is_paused(redis))


def test_while_paused_a_guarded_call_gets_a_503_and_is_recorded(published):
    redis = FakeRedis()
    asyncio.run(refuse_if_paused(redis, "help_chat", user_id="u1"))
    asyncio.run(set_paused(redis, True, "ann"))

    with pytest.raises(HTTPException) as refused:
        asyncio.run(refuse_if_paused(redis, "help_chat", user_id="u1"))

    assert refused.value.status_code == 503
    assert refused.value.detail == PAUSED
    # Only the refusal is a limit hit, not the call made before the pause.
    assert [(kind, data["limit"], data["what"], data["user_id"]) for kind, data in published] == [
        (LIMIT_HIT, PAUSED_LIMIT, "help_chat", "u1")
    ]


def test_with_redis_down_nothing_is_paused():
    assert not asyncio.run(is_paused(DownRedis()))


def test_the_message_has_translations():
    for language in TRANSLATIONS.values():
        assert PAUSED in language
