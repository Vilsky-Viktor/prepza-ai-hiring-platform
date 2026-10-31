"""Events about credits are saved through the outbox with the credits: once, however often
Paddle repeats a top-up or an adjustment, and a bell notice kept until Pub/Sub takes it."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from testee_common.events.notifications import NOTIFICATION_REQUESTED

from billing.constants.events import CREDITS_ADDED
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.models.outbox import OutboxEvent
from billing.repositories.events import tell
from billing.services import topups
from billing.services.adjustments import handle_adjustment
from billing.services.credit_events import credits_added
from tests.unit.paddle_events import adjustment

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
            await topups.grant(
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
                lambda available: events,
            )

        return await saved(acme)

    assert run(scenario()) == events


def test_a_bell_notice_is_kept_in_the_outbox(run):
    notice = {"recipient": "company", "recipient_id": str(uuid.uuid4()), "kind": "x"}

    async def scenario():
        async with Session.begin() as session:
            tell(session, notice)

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


def test_a_reversed_chargeback_paddle_repeats_tells_of_its_credits_once(run):
    """A redelivered adjustment moves no credits, so it publishes nothing again."""
    acme = str(uuid.uuid4())
    txn = f"txn_{uuid.uuid4().hex}"
    reversal = adjustment("chargeback_reverse", total="3000")["data"] | {"transaction_id": txn}

    async def scenario():
        await topups.grant(
            OwnerType.COMPANY, acme, 100, 1, txn, "topup_50", None, "3000", "USD", NOW
        )

        for _ in range(2):
            await handle_adjustment(reversal)

        return [kind for kind, _ in await saved(acme) if kind == CREDITS_ADDED]

    assert run(scenario()) == [CREDITS_ADDED]
