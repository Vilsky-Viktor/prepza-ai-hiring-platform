import pytest

from app.services import delivery
from app.storage import suppressed


@pytest.fixture(autouse=True)
def nothing_suppressed(monkeypatch):
    """No address is on the suppression list unless a test puts it there: unit tests have no
    database (tests/integration checks the real list)."""

    async def get(address):
        return None

    monkeypatch.setattr(suppressed, "get", get)


@pytest.fixture(autouse=True)
def unpaced(monkeypatch):
    """Every request to Resend fits its second, counted nowhere: unit tests have no Redis
    (tests/integration paces against a real one)."""

    async def wait_turn(redis, key, per_second):
        return False

    monkeypatch.setattr(delivery, "wait_turn", wait_turn)
