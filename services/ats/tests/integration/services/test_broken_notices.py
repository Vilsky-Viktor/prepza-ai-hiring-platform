import asyncio
import uuid

import pytest
from sqlalchemy import select

from ats.constants.ats import AtsProvider
from ats.core.db import Session
from ats.handlers.dispatch import handle
from ats.models.outbox import OutboxEvent
from ats.repositories import ats
from ats.services import ats as integrations
from ats.services import outbox as outbox_service
from tests.integration.transactions import transaction


async def broken_notices(company) -> list[dict]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(
                OutboxEvent.data["recipient_id"].astext == str(company),
                OutboxEvent.data["kind"].astext == "connection_broken",
            )
        )

        return list(rows)


@pytest.fixture(autouse=True)
def unsent(monkeypatch):
    """The outbox isn't sent: the notices stay in it, to be read."""

    async def nothing():
        pass

    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)


def test_a_company_is_told_once_each_time_its_ats_connection_stops_working(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)

        # Found broken twice at once, then again: told once.
        await asyncio.gather(*[integrations.mark_broken(connection) for _ in range(2)])
        await integrations.mark_broken(connection)
        once = await broken_notices(company)

        # Reconnected, then broken again: told again.
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-2", "ann")
        await integrations.mark_broken(connection)
        again = len(await broken_notices(company))
        await transaction(ats.delete_company, company)

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
        await transaction(ats.connect, working, AtsProvider.RECRUITEE, "acme", "sealed", maker)
        await transaction(ats.connect, already, AtsProvider.BREEZY, "acme", "sealed", maker)
        await integrations.mark_broken(
            await transaction(ats.connection, already, AtsProvider.BREEZY)
        )
        # Accounts' event, delivered twice: each company is told once.
        for _ in range(2):
            await handle("user.deleted", {"user_id": maker, "email": f"{maker}@x.com"})

        found = (len(await broken_notices(working)), len(await broken_notices(already)))
        kept = await transaction(ats.connection, already, AtsProvider.BREEZY)
        await transaction(ats.delete_company, working)
        await transaction(ats.delete_company, already)

        return found, kept

    (working, already), kept = run(scenario())

    # The one already broken was told when it broke, not again.
    assert (working, already) == (1, 1)
    assert kept.created_by != "" and not kept.created_by.startswith("maker-")
