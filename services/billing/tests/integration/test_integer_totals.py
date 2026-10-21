"""Money is kept as an integer (migration 0020): new top-ups and refunds write it, and a row an
older version wrote with only the text total still reads the same."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.constants.products import OwnerType
from app.helpers.history import history_entry_out
from app.models.billing import Entry, Purchase
from app.storage import history, purchases
from app.storage.db import Session

COMPANY = OwnerType.COMPANY
NOW = datetime.now(UTC)


def test_a_top_up_keeps_its_total_as_an_integer(run):
    acme = str(uuid.uuid4())
    transaction = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(
            COMPANY, acme, 5_000, 1, transaction, "topup_50", "ann", "5550", "USD", NOW
        )

        async with Session() as session:
            bought = await session.scalar(
                select(Purchase.total_minor).where(Purchase.transaction_id == transaction)
            )
            entry = await session.scalar(
                select(Entry.total_minor).where(Entry.key == f"{transaction}:topup_50")
            )

        return bought, entry

    assert run(scenario()) == (5550, 5550)


def test_a_row_an_older_version_wrote_reads_the_same(run):
    """During a deploy the old version writes only the text total."""
    acme = str(uuid.uuid4())
    ann = f"user-{uuid.uuid4()}"
    transaction = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(
            COMPANY, acme, 5_000, 1, transaction, "topup_50", ann, "750", "JPY", NOW
        )

        async with Session() as session:
            await session.execute(
                update(Purchase)
                .where(Purchase.transaction_id == transaction)
                .values(total_minor=None)
            )
            await session.execute(
                update(Entry).where(Entry.key == f"{transaction}:topup_50").values(total_minor=None)
            )
            await session.commit()

        owner = await purchases.for_transaction(transaction)
        [listed] = await purchases.bought_by(ann, 10)
        [entry] = await history.page(COMPANY, acme, 0, 1)

        return owner[3], listed.total, history_entry_out(entry).total

    # Refunds' shares, the support tab and the company's history all see 750 yen.
    assert run(scenario()) == (750, 750, "750")
