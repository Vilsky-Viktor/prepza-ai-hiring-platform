import asyncio
import uuid

from assistant.handlers import company_deleted, dispatch

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")


def test_only_company_deleted_is_handled_and_a_malformed_one_is_dropped(monkeypatch):
    deleted = []

    async def delete_company(company_id):
        deleted.append(company_id)

        return 0

    monkeypatch.setattr(company_deleted.conversations, "delete_company", delete_company)
    asyncio.run(dispatch.handle("interview.deleted", {"interview_id": str(COMPANY)}))
    asyncio.run(dispatch.handle("company.deleted", {"company_id": "not-a-uuid"}))
    asyncio.run(dispatch.handle("company.deleted", {"company_id": str(COMPANY)}))

    assert deleted == [COMPANY]
