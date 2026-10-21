import uuid
from datetime import UTC, datetime, timedelta

from app.constants.credits import CANDIDATE_CREDITS, Reason
from app.constants.products import TOP_UPS, OwnerType
from app.storage import ledger, purchases, stats

COMPANY = OwnerType.COMPANY


def test_a_transaction_counts_once_and_spent_credits_are_charges_only(run):
    acme = str(uuid.uuid4())
    now = datetime.now(UTC)
    month = now.strftime("%Y-%m")

    async def scenario():
        before = await stats.stats(month)
        transaction = f"txn_{uuid.uuid4().hex}"

        # Two product lines of one $49 transaction: each holds the whole total.
        for top_up in TOP_UPS[:2]:
            await purchases.grant(
                COMPANY, acme, 10_000, 1, transaction, top_up.key, None, "4900", "USD", now
            )

        # One in euros this month, counted apart.
        await purchases.grant(
            COMPANY, acme, 100, 1, f"txn_{uuid.uuid4().hex}", "topup_50", None, "5950", "EUR", now
        )
        # One paid last month.
        last_month = now.replace(day=1) - timedelta(days=1)
        await purchases.grant(
            COMPANY,
            acme,
            100,
            1,
            f"txn_{uuid.uuid4().hex}",
            "topup_50",
            None,
            "3000",
            "USD",
            last_month,
        )
        # One candidate charged, one released: only the charge is spent.
        charged, released = f"candidate:{uuid.uuid4()}", f"candidate:{uuid.uuid4()}"

        for key in (charged, released):
            await ledger.reserve(COMPANY, acme, CANDIDATE_CREDITS, key, Reason.CANDIDATE)

        await ledger.charge(charged)
        await ledger.release(released)
        after = await stats.stats(month)

        return [{name: now[name] - then[name] for name in now} for now, then in zip(after, before)]

    counts, paid = run(scenario())

    assert counts == {"top_ups": 2, "credits_spent": CANDIDATE_CREDITS}
    assert paid == {"USD": 4900, "EUR": 5950, "GBP": 0}
