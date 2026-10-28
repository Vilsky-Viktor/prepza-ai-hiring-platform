import pytest
from no_publishing import published  # noqa: F401
from prepza_common.redis import memory_cache


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    """Each test reads the limits afresh, not a value an earlier test cached."""
    monkeypatch.setattr(memory_cache, "_entries", {})
