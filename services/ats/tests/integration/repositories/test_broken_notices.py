import asyncio
import uuid

from sqlalchemy import select

from ats.constants.ats import AtsProvider
from ats.core.db import Session
from ats.models.outbox import OutboxEvent
from ats.repositories import ats


async def broken_notices(company) -> list[dict]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(
                OutboxEvent.data["recipient_id"].astext == str(company),
                OutboxEvent.data["kind"].astext == "connection_broken",
            )
        )

        return list(rows)


def test_a_company_is_told_once_each_time_its_ats_connection_stops_working(run):
    async def scenario():
        company = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await ats.connection(company, AtsProvider.WORKABLE)

        # Found broken twice at once, then again: told once.
        await asyncio.gather(*[ats.mark_broken(connection.id) for _ in range(2)])
        await ats.mark_broken(connection.id)
        once = await broken_notices(company)

        # Reconnected, then broken again: told again.
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed-2", "ann")
        await ats.mark_broken(connection.id)
        again = len(await broken_notices(company))
        await ats.delete_company(company)

        return once, again

    once, again = run(scenario())

    [notice] = once
    assert notice["data"] == {"name": "Workable", "integration": "ats"}
    assert notice["link"].endswith("/integrations/workable")
    assert again == 2


def test_deleting_an_account_tells_each_company_whose_connection_it_stops(run):
    async def scenario():
        maker = f"maker-{uuid.uuid4()}"
        working, already = uuid.uuid4(), uuid.uuid4()
        await ats.connect(working, AtsProvider.RECRUITEE, "acme", "sealed", maker)
        await ats.connect(already, AtsProvider.BREEZY, "acme", "sealed", maker)
        await ats.mark_broken((await ats.connection(already, AtsProvider.BREEZY)).id)
        await ats.forget_maker(maker)
        found = (len(await broken_notices(working)), len(await broken_notices(already)))
        kept = await ats.connection(already, AtsProvider.BREEZY)
        await ats.delete_company(working)
        await ats.delete_company(already)

        return found, kept

    (working, already), kept = run(scenario())

    # The one already broken was told when it broke, not again.
    assert (working, already) == (1, 1)
    assert kept.created_by != "" and not kept.created_by.startswith("maker-")
