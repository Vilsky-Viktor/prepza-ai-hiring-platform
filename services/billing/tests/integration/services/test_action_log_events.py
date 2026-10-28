"""A member's top-up reaches the company's action log through billing's outbox: saved with the
purchase, once however often Paddle retries, never for an automatic top-up."""

import uuid
from datetime import UTC, datetime

from prepza_common.events.audit_actions import AUDIT_RECORDED
from sqlalchemy import select

from billing.constants.products import TOP_UPS, OwnerType
from billing.core.db import Session
from billing.models.outbox import OutboxEvent
from billing.services import topups
from tests.integration.factories import welcomed

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)
TOPUP = TOP_UPS[0]


async def logged(company: str) -> list[dict]:
    """The company's actions waiting in the outbox for its action log, oldest first."""
    query = (
        select(OutboxEvent.data)
        .where(
            OutboxEvent.event_type == AUDIT_RECORDED,
            OutboxEvent.data["company_id"].astext == company,
        )
        .order_by(OutboxEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


def test_a_members_top_up_is_logged_once_and_an_automatic_one_not(run):
    acme = str(uuid.uuid4())
    paid, automatic = f"txn_{uuid.uuid4().hex}", f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")

        for _ in range(2):
            await topups.grant(
                OwnerType.COMPANY, acme, 1_000, 1, paid, TOPUP.key, "ann", "1000", "USD", NOW
            )

        await topups.grant(
            OwnerType.COMPANY,
            acme,
            1_000,
            1,
            automatic,
            TOPUP.key,
            "ann",
            "1000",
            "USD",
            NOW,
            automatic=True,
        )

        return await logged(acme)

    events = run(scenario())

    assert [(row["action"], row["user_id"], row["target_kind"]) for row in events] == [
        ("top_up_paid", "ann", "company")
    ]
