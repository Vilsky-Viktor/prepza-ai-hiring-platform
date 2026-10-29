import asyncio
import uuid

from event_pushes import push
from fastapi.testclient import TestClient

from assistant.handlers import company_deleted, dispatch, user_deleted
from assistant.main import app

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")


def deletions(monkeypatch):
    deleted = []

    async def delete_company(company_id):
        deleted.append(company_id)

        return 0

    monkeypatch.setattr(company_deleted.conversations, "delete_company", delete_company)

    return deleted


def test_only_company_deleted_is_handled(monkeypatch):
    deleted = deletions(monkeypatch)
    asyncio.run(dispatch.handle("interview.deleted", {"interview_id": str(COMPANY)}))
    asyncio.run(dispatch.handle("company.deleted", {"company_id": str(COMPANY)}))

    assert deleted == [COMPANY]


def test_an_event_with_a_malformed_company_is_acknowledged_and_deletes_nothing(monkeypatch):
    deleted = deletions(monkeypatch)
    data = {"company_id": "not-a-uuid"}

    assert (
        TestClient(app).post("/internal/events", json=push("company.deleted", data)).status_code
        == 204
    )
    assert deleted == []


def test_a_deleted_account_takes_its_conversations_and_apps_and_a_malformed_one_is_dropped(
    monkeypatch,
):
    deleted = []

    async def delete_user(user_id):
        deleted.append(user_id)

    monkeypatch.setattr(user_deleted.accounts, "delete_user", delete_user)
    client = TestClient(app)
    gone = push("user.deleted", {"user_id": "ann", "email": "ann@example.com"})

    assert client.post("/internal/events", json=gone).status_code == 204
    assert client.post("/internal/events", json=push("user.deleted", {})).status_code == 204
    assert deleted == ["ann"]
