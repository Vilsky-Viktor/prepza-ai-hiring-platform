"""Events about credits are saved through the outbox with the credits: once, however often
Paddle repeats a top-up, and a bell notice kept until Pub/Sub takes it."""

import uuid
from datetime import UTC, datetime

from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import select

from app.constants.products import OwnerType
from app.models.outbox import OutboxEvent
from app.services.credit_events import credits_added
from app.storage import purchases
from app.storage.db import Session
from app.storage.events import tell

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


async def saved(owner_id: str) -> list[tuple[str, dict]]:
    query = select(OutboxEvent.event_type, OutboxEvent.data).where(
        OutboxEvent.data["owner_id"].astext == owner_id
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


def test_a_top_up_saves_its_event_once_however_often_paddle_repeats_it(run):
    acme = str(uuid.uuid4())
    transaction = f"txn_{uuid.uuid4().hex}"
    events = [credits_added(OwnerType.COMPANY, acme)]

    async def scenario():
        for _ in range(2):
            await purchases.grant(
                OwnerType.COMPANY,
                acme,
                100,
                1,
                transaction,
                "topup_50",
                None,
                "3000",
                "USD",
                NOW,
                False,
                events,
            )

        return await saved(acme)

    assert run(scenario()) == events


def test_a_bell_notice_is_kept_in_the_outbox(run):
    notice = {"recipient": "company", "recipient_id": str(uuid.uuid4()), "kind": "x"}

    async def scenario():
        await tell(notice)

        async with Session() as session:
            return list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == NOTIFICATION_REQUESTED,
                        OutboxEvent.data["recipient_id"].astext == notice["recipient_id"],
                    )
                )
            )

    assert run(scenario()) == [notice]
