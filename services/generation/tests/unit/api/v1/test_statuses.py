import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer

from generation.repositories import generations

TOKEN = issue_token("notifications", "generation", "test-secret-that-is-at-least-32-bytes")


def test_statuses_say_who_started_each_generation_and_since_when(client, monkeypatch):
    found = SimpleNamespace(
        id=uuid.uuid4(),
        status="awaiting_review",
        owner_uid="ann",
        updated_at=datetime(2026, 10, 7, tzinfo=UTC),
    )

    async def by_ids(session, ids):
        return [found]

    monkeypatch.setattr(generations, "by_ids", by_ids)

    response = client.post(
        "/internal/generations/statuses",
        json={"ids": [str(found.id), str(uuid.uuid4())]},
        headers=bearer(TOKEN),
    )

    assert response.json() == {
        "generations": [
            {
                "id": str(found.id),
                "status": "awaiting_review",
                "owner_uid": "ann",
                "updated_at": "2026-10-07T00:00:00Z",
            }
        ]
    }
