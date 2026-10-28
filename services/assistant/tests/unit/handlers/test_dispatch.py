import asyncio
import uuid

from event_pushes import push
from fastapi.testclient import TestClient

from assistant.handlers import company_deleted, dispatch
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
