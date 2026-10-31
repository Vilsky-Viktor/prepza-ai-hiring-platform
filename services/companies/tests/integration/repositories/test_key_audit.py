import uuid

from sqlalchemy import select
from testee_common.auth.key_actor import key_actor
from testee_common.config.constants import VIA_MCP

from companies.core.db import Session
from companies.core.security import REQUEST_VIA
from companies.models.audit import AuditEvent
from companies.repositories import audit
from tests.integration import factories
from tests.integration.transactions import transaction


def test_an_action_by_an_api_key_is_saved_as_the_keys_never_a_persons(run):
    key_id = uuid.uuid4()

    async def scenario():
        company = await factories.company(f"Key audit {uuid.uuid4()}", "ann", "ann@example.com")
        via = REQUEST_VIA.set(VIA_MCP)

        try:
            await transaction(audit.record, company.id, key_actor(key_id), "results_viewed")
        finally:
            REQUEST_VIA.reset(via)

        await transaction(audit.record, company.id, "ann", "results_viewed")

        async with Session() as session:
            rows = await session.execute(
                select(AuditEvent.user_id, AuditEvent.key_id, AuditEvent.via)
                .where(AuditEvent.company_id == company.id)
                .order_by(AuditEvent.created_at)
            )
            saved = [tuple(row) for row in rows]

        await factories.deleted(company.id)

        return saved

    assert run(scenario()) == [(key_actor(key_id), key_id, VIA_MCP), ("ann", None, None)]
