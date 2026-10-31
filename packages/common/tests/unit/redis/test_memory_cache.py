import time

from testee_common.redis import memory_cache


def test_a_value_is_kept_until_it_expires_and_expired_ones_go(monkeypatch):
    now = time.monotonic()
    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr(time, "monotonic", lambda: now)
    memory_cache.put("a", {"title": "Backend"}, 30)
    memory_cache.put("b", 1, 5)
    kept = memory_cache.get("a")

    monkeypatch.setattr(time, "monotonic", lambda: now + 10)
    memory_cache.put("c", 2, 5)

    assert kept == {"title": "Backend"}
    assert memory_cache.get("a") == {"title": "Backend"}
    assert memory_cache.get("b") is None and "b" not in memory_cache._entries
