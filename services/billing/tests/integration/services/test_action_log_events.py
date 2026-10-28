"""A member's payment actions reach the company's action log through billing's outbox, saved
with their change: a top-up (once however often Paddle retries, never an automatic one), the
currency and the automatic top-up."""

import uuid
from datetime import UTC, datetime

from prepza_common.events.audit_actions import AUDIT_RECORDED
from sqlalchemy import select

from billing.constants.currencies import Currency
from billing.constants.products import TOP_UPS, OwnerType
from billing.core.db import Session
from billing.models.outbox import OutboxEvent
from billing.schemas.billing import AutoTopUpIn
from billing.services import auto_top_ups, currencies, topups
from tests.integration.factories import welcomed
from tests.integration.services.test_auto_top_ups import checkout_data

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


def test_a_members_currency_and_automatic_top_up_changes_are_logged_with_them(run, paddle_calls):
    """Billing checks the member itself now, so it logs their choices in the same saves: the
    currency, the automatic top-up set up, changed once running, and turned off. A change made
    for no member (a removed member's card, the company deleted) logs nothing."""
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    choice = AutoTopUpIn(product="topup_50", threshold=500)

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await currencies.choose_company(acme, Currency.EUR, ann)
        await currencies.choose_company(acme, Currency.USD)
        await auto_top_ups.turn_on(OwnerType.COMPANY, acme, choice, ann, Currency.EUR, logged=True)
        await auto_top_ups.start(checkout_data(acme, ann), f"sub_{uuid.uuid4().hex[:12]}", "EUR")
        await auto_top_ups.turn_on(OwnerType.COMPANY, acme, choice, ann, Currency.EUR, logged=True)
        await auto_top_ups.turn_off(OwnerType.COMPANY, acme, actor=ann)
        # Already off: nothing changes, nothing is logged.
        await auto_top_ups.turn_off(OwnerType.COMPANY, acme, actor=ann)

        return await logged(acme)

    events = run(scenario())

    assert [(row["action"], row["user_id"], row["target_id"]) for row in events] == [
        (action, ann, acme)
        for action in (
            "currency_changed",
            "auto_top_up_set",
            "auto_top_up_changed",
            "auto_top_up_stopped",
        )
    ]
