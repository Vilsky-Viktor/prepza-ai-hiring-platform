"""Money is kept as an integer in minor units (migrations 0020, 0021): top-ups and refunds write
it, the API gives it as a string, and the database refuses a purchase without one."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.constants.products import OwnerType
from app.helpers.history import history_entry_out
from app.models.billing import Purchase
from app.storage import history, purchases
from app.storage.db import Session

COMPANY = OwnerType.COMPANY
NOW = datetime.now(UTC)


def test_a_top_up_keeps_its_total_as_an_integer_and_the_api_as_a_string(run):
    acme = str(uuid.uuid4())
    ann = f"user-{uuid.uuid4()}"
    transaction = f"txn_{uuid.uuid4().hex}"

    async def scenario():
        await purchases.grant(
            COMPANY, acme, 5_000, 1, transaction, "topup_50", ann, "750", "JPY", NOW
        )

        async with Session() as session:
            stored = await session.scalar(
                select(Purchase.total_minor).where(Purchase.transaction_id == transaction)
            )

        owner = await purchases.for_transaction(transaction)
        [listed] = await purchases.bought_by(ann, 10)
        [entry] = await history.page(COMPANY, acme, 0, 1)

        return stored, owner[3], listed.total, history_entry_out(entry).total

    # Stored, used for refunds' shares and the support tab as 750 yen; the history's API a string.
    assert run(scenario()) == (750, 750, 750, "750")


def test_a_purchase_without_its_total_is_refused(run):
    async def scenario():
        async with Session() as session:
            await session.execute(
                insert(Purchase).values(
                    transaction_id=f"txn_{uuid.uuid4().hex}",
                    product="topup_50",
                    quantity=1,
                    owner_type=COMPANY,
                    owner_id=str(uuid.uuid4()),
                    currency="USD",
                )
            )
            await session.commit()

    with pytest.raises(IntegrityError):
        run(scenario())
