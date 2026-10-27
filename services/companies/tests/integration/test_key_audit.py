import uuid

from prepza_common.config.constants import VIA_MCP
from sqlalchemy import select

from app.models.audit import AuditEvent
from app.service_auth import REQUEST_KEY, REQUEST_VIA
from app.storage import audit, companies
from app.storage.db import Session


def test_an_action_through_an_api_key_is_saved_with_the_key(run):
    key_id = uuid.uuid4()

    async def scenario():
        company = await companies.create(f"Key audit {uuid.uuid4()}", "ann", "ann@example.com")
        key = REQUEST_KEY.set(str(key_id))
        via = REQUEST_VIA.set(VIA_MCP)

        try:
            await audit.record(company.id, "ann", "results_viewed")
        finally:
            REQUEST_KEY.reset(key)
            REQUEST_VIA.reset(via)

        await audit.record(company.id, "ann", "results_viewed")

        async with Session() as session:
            rows = await session.execute(
                select(AuditEvent.key_id, AuditEvent.via)
                .where(AuditEvent.company_id == company.id)
                .order_by(AuditEvent.created_at)
            )
            saved = [tuple(row) for row in rows]

        await companies.delete(company.id)

        return saved

    assert run(scenario()) == [(key_id, VIA_MCP), (None, None)]
