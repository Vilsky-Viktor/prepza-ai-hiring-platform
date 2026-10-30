"""Automatic top-up's consent and notices against Postgres: the tick and its time kept with the
setting and the terms in the action log; one "turned on" notice per subscription, even when
Paddle's two events for the checkout race or come again; one "charged" notice per charge, with
the credits available after it, however often Paddle sends the payment; and a cancel made in
Paddle turning it off at once."""

import os
import uuid
from datetime import UTC, datetime

from prepza_common.db.lock_waits import hold_first_commit, race
from prepza_common.events.audit_actions import AUDIT_RECORDED
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import select

from billing.constants.credits import WELCOME_COMPANY
from billing.constants.currencies import Currency
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.models.outbox import OutboxEvent
from billing.repositories import auto_top_ups as rows
from billing.schemas.billing import AutoTopUpIn
from billing.services import auto_top_ups, webhooks
from billing.services.topups import handle_completed
from tests.integration import transactions
from tests.integration.conftest import charged
from tests.integration.factories import welcomed
from tests.integration.services.test_auto_top_ups import checkout_data

COMPANY = OwnerType.COMPANY
CHOICE = AutoTopUpIn(product="topup_50", threshold=1_500, agreed=True)


async def outbox(company: str, event_type: str) -> list[dict]:
    """The company's events waiting in the outbox, oldest first."""
    key = "recipient_id" if event_type == NOTIFICATION_REQUESTED else "company_id"
    query = (
        select(OutboxEvent.data)
        .where(OutboxEvent.event_type == event_type, OutboxEvent.data[key].astext == company)
        .order_by(OutboxEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def notices(company: str, kind: str) -> list[dict]:
    return [row for row in await outbox(company, NOTIFICATION_REQUESTED) if row["kind"] == kind]


def test_the_tick_is_kept_with_when_and_the_terms_agreed_to(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        before = datetime.now(UTC)
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.EUR, "de", logged=True)
        row = await transactions.transaction(rows.get, COMPANY, acme)

        return before, row, await outbox(acme, AUDIT_RECORDED)

    before, row, logged = run(scenario())

    assert before <= row.agreed_at <= datetime.now(UTC)
    assert row.buyer_id == ann
    [entry] = logged
    assert (entry["action"], entry["user_id"]) == ("auto_top_up_set", ann)
    # What the dialog showed: the price in the company's currency and the level, in German.
    assert "50\u00a0€" in entry["target_label"]
    assert "1.500" in entry["target_label"]


def test_paddles_two_checkout_events_at_once_attach_the_card_once(run, monkeypatch):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        held = hold_first_commit(monkeypatch, transactions)
        start = (rows.start, COMPANY, acme, ann, sub, "USD")

        return await race(
            os.environ["DATABASE_URL"],
            held,
            transactions.transaction(*start),
            transactions.transaction(*start),
        )

    (first, attached), (second, again) = run(scenario())

    # Both count as started; only the first attached it, so only it confirms it.
    assert first and second
    assert attached is not None and attached.subscription_id == sub
    assert again is None


def test_turning_it_on_is_confirmed_once_with_its_terms(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.EUR)

        # subscription.created and transaction.completed for the same checkout, then a
        # redelivery: one notice.
        for _ in range(3):
            await auto_top_ups.start(checkout_data(acme, ann), sub, "EUR")

        return await notices(acme, "auto_top_up_on")

    [notice] = run(scenario())

    assert notice["key"] == f"auto_top_up_on:{sub}"
    assert notice["link"] == f"/companies/{acme}/billing"
    assert notice["data"] == {"price": 5_000, "currency": "EUR", "threshold": 1_500}


def test_a_charge_paddle_sends_again_is_announced_once_with_the_balance_after_it(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    sub = f"sub_{uuid.uuid4().hex[:12]}"

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")
        payment = charged(sub, subtotal="5450")
        payment["billed_at"] = "2026-10-29T23:10:00Z"

        # Paddle's web hook, its retry, and the daily reconciliation's replay.
        for _ in range(3):
            await handle_completed(payment)

        return payment["id"], await notices(acme, "auto_top_up_charged")

    transaction_id, [notice] = run(scenario())

    assert notice["key"] == f"auto_top_up_charged:{transaction_id}"
    assert notice["link"] == f"/companies/{acme}/billing"
    # 5,000 credits bought on top of the welcome credits, none set aside.
    assert notice["data"] == {
        "credits": 5_000,
        "price": 5_450,
        "currency": "USD",
        "date": "2026-10-29",
        "available": WELCOME_COMPANY + 5_000,
    }


def test_a_cancel_made_in_paddle_turns_it_off_at_once(run, paddle_calls):
    acme, ann = str(uuid.uuid4()), f"user-{uuid.uuid4()}"
    sub = f"sub_{uuid.uuid4().hex[:12]}"
    event = {
        "event_type": "subscription.updated",
        "data": {"id": sub, "status": "active", "scheduled_change": {"action": "cancel"}},
    }

    async def scenario():
        await welcomed(acme, f"{acme}@example.com")
        await auto_top_ups.turn_on(COMPANY, acme, CHOICE, ann, Currency.USD)
        await auto_top_ups.start(checkout_data(acme, ann), sub, "USD")

        # Paddle's event and its redelivery.
        for _ in range(2):
            await webhooks.handle(event)

        return await auto_top_ups.out(COMPANY, acme, Currency.USD)

    setting = run(scenario())

    assert not setting.on and not setting.waiting
    assert paddle_calls.count(("cancel", sub)) == 1
