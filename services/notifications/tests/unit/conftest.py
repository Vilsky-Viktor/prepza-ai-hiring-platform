import pytest

from app.storage import suppressed


@pytest.fixture(autouse=True)
def nothing_suppressed(monkeypatch):
    """No address is on the suppression list unless a test puts it there: unit tests have no
    database (tests/integration checks the real list)."""

    async def get(address):
        return None

    monkeypatch.setattr(suppressed, "get", get)
