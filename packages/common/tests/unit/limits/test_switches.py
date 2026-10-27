"""Switches (the pause, maintenance mode): read through the per-instance cache, and with Redis
down they keep the last state this instance read."""

import asyncio

from fake_redis import DownRedis, FakeRedis
from prepza_common.limits import switches
from prepza_common.redis import memory_cache

KEY = "switch:on"


def test_a_switch_is_read_from_redis_once_a_while():
    redis = FakeRedis()
    redis.counts[KEY] = "ann"

    assert asyncio.run(switches.is_on(redis, KEY, 5)) is True

    # Turned off elsewhere: this instance still holds its read for the cache's time.
    del redis.counts[KEY]

    assert asyncio.run(switches.is_on(redis, KEY, 5)) is True


def test_with_redis_down_a_switch_keeps_the_last_state_read():
    redis = FakeRedis()
    redis.counts[KEY] = "ann"
    asyncio.run(switches.is_on(redis, KEY, 5))
    # The cached read expires; then Redis goes down.
    memory_cache._entries.pop(KEY)

    assert asyncio.run(switches.is_on(DownRedis(), KEY, 5)) is True


def test_a_switch_never_read_is_off_while_redis_is_down():
    assert asyncio.run(switches.is_on(DownRedis(), KEY, 5)) is False


def test_the_instance_that_turns_it_knows_at_once():
    switches.remember(KEY, True, 5)

    assert asyncio.run(switches.is_on(DownRedis(), KEY, 5)) is True
