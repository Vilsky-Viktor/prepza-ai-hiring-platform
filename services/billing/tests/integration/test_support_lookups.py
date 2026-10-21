"""What the admin zone's support tab asks billing about a person and a candidate, against the
real database."""

import uuid
from datetime import UTC, datetime, timedelta

from app.constants.credits import CANDIDATE_CREDITS, HoldStatus, Reason
from app.constants.products import TOP_UPS, OwnerType
from app.storage import ledger, purchases

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)
COMPANY = OwnerType.COMPANY


def test_a_persons_top_ups_once_per_transaction_newest_first(run):
    acme, buyer, other = str(uuid.uuid4()), f"ann-{uuid.uuid4().hex}", f"bob-{uuid.uuid4().hex}"
    first, second, theirs = (f"txn_{uuid.uuid4().hex}" for _ in range(3))

    async def scenario():
        # One transaction of two lines, a later one, and another person's.
        for product in (TOP_UPS[0].key, TOP_UPS[1].key):
            await purchases.grant(
                COMPANY, acme, 1_000, 1, first, product, buyer, "25000", "USD", NOW
            )

        later = NOW + timedelta(days=1)
        await purchases.grant(
            COMPANY, acme, 1_000, 1, second, "topup_50", buyer, "5000", "EUR", later
        )
        await purchases.grant(
            COMPANY, acme, 1_000, 1, theirs, "topup_50", other, "5000", "USD", NOW
        )

        return await purchases.bought_by(buyer, 100), await purchases.bought_by(buyer, 1)

    found, limited = run(scenario())

    assert [tuple(row) for row in found] == [
        (second, acme, 5000, "EUR", NOW + timedelta(days=1)),
        (first, acme, 25000, "USD", NOW),
    ]
    assert [row.transaction_id for row in limited] == [second]


def test_a_candidates_hold_is_open_then_charged_or_released(run):
    acme = str(uuid.uuid4())
    charged, released = f"candidate:{uuid.uuid4().hex}", f"candidate:{uuid.uuid4().hex}"

    async def scenario():
        await ledger.welcome_company(acme, f"{acme}@example.com")
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, charged, Reason.CANDIDATE)
        await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, released, Reason.CANDIDATE)
        held = await ledger.hold_status(charged)
        await ledger.charge(charged)
        await ledger.release(released)

        return (
            held,
            await ledger.hold_status(charged),
            await ledger.hold_status(released),
            await ledger.hold_status("candidate:none"),
        )

    assert run(scenario()) == (HoldStatus.OPEN, HoldStatus.CHARGED, HoldStatus.RELEASED, None)
