import pytest
from fake_redis import FakeRedis
from prepza_common.redis import memory_cache

# The modules that reach Redis, which unit tests replace.
REDIS_USERS = [
    "site_content.services.contact",
    "site_content.services.help",
]


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    """Redis in memory: the limits count in it, and a test edits a limit in `limits`. Each test
    reads the limits afresh, not a value an earlier test cached."""
    fake = FakeRedis()
    monkeypatch.setattr(memory_cache, "_entries", {})

    for module in REDIS_USERS:
        monkeypatch.setattr(f"{module}.get_redis", lambda: fake)

    return fake
