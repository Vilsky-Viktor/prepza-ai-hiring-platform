import pytest
from fake_redis import FakeRedis
from prepza_common.redis import memory_cache

from rounds.repositories import session_expiry

# The modules that reach Redis, which unit tests replace.
REDIS_USERS = [
    "rounds.api.v1.practice",
    "rounds.services.practice",
    "rounds.services.signals",
    "rounds.services.voice_clips",
    "rounds.services.voice_limits",
]


@pytest.fixture(autouse=True)
def nothing_expired(monkeypatch):
    """Opening a session checks whether the whole interview ran out of time, in the database;
    unit tests have none, so nothing has expired unless a test says so."""

    async def none_expired(session, now, limit, invite_id=None):
        return []

    monkeypatch.setattr(session_expiry, "expired_invites", none_expired)


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    """Redis in memory: the limits count in it, and a test edits a limit in `limits`. Each test
    reads the limits afresh, not a value an earlier test cached."""
    fake = FakeRedis()
    monkeypatch.setattr(memory_cache, "_entries", {})

    for module in REDIS_USERS:
        monkeypatch.setattr(f"{module}.get_redis", lambda: fake)

    return fake
