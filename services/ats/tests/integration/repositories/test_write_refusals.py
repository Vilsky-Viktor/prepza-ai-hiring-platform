import asyncio
import uuid

from sqlalchemy import func, select

from ats.constants.ats import AtsProvider
from ats.core.db import Session
from ats.models.outbox import OutboxEvent
from ats.repositories import ats
from tests.integration.transactions import transaction


async def notices(company) -> int:
    async with Session() as session:
        return await session.scalar(
            select(func.count())
            .select_from(OutboxEvent)
            .where(OutboxEvent.data["recipient_id"].astext == str(company))
        )


def test_a_company_hears_once_that_its_ats_refuses_results_until_it_reconnects(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.RECRUITEE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.RECRUITEE)
        notice = {"recipient_id": str(company), "kind": "ats_cannot_write"}

        # Two refused results at once, then another later: one notice.
        await asyncio.gather(
            *[transaction(ats.refuse_writes, connection.id, notice) for _ in range(2)]
        )
        await transaction(ats.refuse_writes, connection.id, notice)
        once = await notices(company)

        # A reconnect (a new key) may write: a refusal is told again.
        await transaction(ats.connect, company, AtsProvider.RECRUITEE, "acme", "sealed-2", "ann")
        await transaction(ats.refuse_writes, connection.id, notice)
        again = await notices(company)
        await transaction(ats.delete_company, company)

        return once, again

    assert run(scenario()) == (1, 2)
