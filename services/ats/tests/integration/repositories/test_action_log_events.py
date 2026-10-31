"""A member's ATS actions reach the company's action log through ats' outbox, saved with the
change itself: connecting, reconnecting, linking and unlinking a job, and disconnecting. What
changes nothing isn't logged."""

import uuid

from sqlalchemy import select
from testee_common.events.audit_actions import AUDIT_RECORDED

from ats.constants.ats import AtsProvider
from ats.core.db import Session
from ats.models.outbox import OutboxEvent
from ats.repositories import ats, ats_links
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


async def logged(company) -> list[dict]:
    """The company's actions waiting in the outbox for its action log, oldest first."""
    query = (
        select(OutboxEvent.data)
        .where(
            OutboxEvent.event_type == AUDIT_RECORDED,
            OutboxEvent.data["company_id"].astext == str(company),
        )
        .order_by(OutboxEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


def test_a_members_ats_actions_are_logged_with_what_they_were_about(run):
    company, interview = uuid.uuid4(), uuid.uuid4()

    async def scenario():
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-2", "bob")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link = await transaction(
            ats_links.add_link, company, connection.id, interview, JOB, STAGE, "ann"
        )
        # Already linked: nothing more.
        await transaction(ats_links.add_link, company, connection.id, interview, JOB, STAGE, "ann")
        await transaction(ats_links.remove_link, company, link, "bob")
        await transaction(ats_links.remove_link, company, link, "bob")
        await transaction(ats.disconnect, company, AtsProvider.WORKABLE, "ann")
        # Nothing left to disconnect.
        await transaction(ats.disconnect, company, AtsProvider.WORKABLE, "ann")

        return await logged(company)

    events = run(scenario())

    assert [(row["action"], row["user_id"], row["target_label"]) for row in events] == [
        ("ats_connected", "ann", "Workable"),
        ("ats_reconnected", "bob", "Workable"),
        ("job_linked", "ann", "Accountant"),
        ("job_unlinked", "bob", "Accountant"),
        ("ats_disconnected", "ann", "Workable"),
    ]
    assert {row["target_kind"] for row in events} == {"integration"}


def test_two_connects_at_once_log_one_connect_and_one_reconnect(run):
    import asyncio

    company = uuid.uuid4()

    async def scenario():
        await asyncio.gather(
            transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann"),
            transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed-2", "bob"),
        )

        return sorted(entry["action"] for entry in await logged(company))

    assert run(scenario()) == ["ats_connected", "ats_reconnected"]
