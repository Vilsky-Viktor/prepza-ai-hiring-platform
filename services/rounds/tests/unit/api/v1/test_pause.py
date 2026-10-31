import uuid

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.config.constants import PAUSED

from rounds.main import app


@pytest.fixture(autouse=True)
def paused(monkeypatch):
    async def on(redis):
        return True

    monkeypatch.setattr("testee_common.limits.pause.is_paused", on)
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


def test_paused_no_practice_round_starts(client):
    refused = client.post(f"/practice/{uuid.uuid4()}")

    assert refused.status_code == 503
    assert refused.json()["detail"] == PAUSED
