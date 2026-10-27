"""A deleted company's ledger goes a batch at a time, each batch its own transaction: every
hold and entry, then the wallet; another company's stays."""

import uuid

from prepza_common.db import db
from sqlalchemy import func, select

from app.constants.credits import Reason
from app.constants.products import OwnerType
from app.models.billing import Entry, Hold, Wallet
from app.storage import ledger, purchases
from app.storage.db import Session

COMPANY = OwnerType.COMPANY


async def ledger_rows(company_id: str) -> list[int]:
    """How many holds, entries and wallets the company has."""
    async with Session() as session:
        return [
            await session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.owner_type == COMPANY, model.owner_id == company_id)
            )
            for model in (Hold, Entry, Wallet)
        ]


async def company_with_ledger() -> str:
    """A company with its welcome gift, five holds and three charges."""
    company_id = str(uuid.uuid4())
    await ledger.welcome_company(company_id, f"{company_id}@example.com")

    for number in range(5):
        key = f"candidate:{company_id}:{number}"
        await ledger.reserve(COMPANY, company_id, 1, key, Reason.CANDIDATE)

        if number < 3:
            await ledger.charge(key)

    return company_id


def test_a_deleted_companys_ledger_goes_batch_after_batch(run, monkeypatch):
    monkeypatch.setattr(db, "DELETE_BATCH", 2)

    async def scenario():
        acme, other = await company_with_ledger(), await company_with_ledger()
        before = await ledger_rows(acme)
        await purchases.delete_company(acme)
        after, kept = await ledger_rows(acme), await ledger_rows(other)
        await purchases.delete_company(other)

        return before, after, kept

    before, after, kept = run(scenario())

    # More holds and entries than a batch, all gone; the other company's all there.
    assert before == [5, 4, 1]
    assert after == [0, 0, 0]
    assert kept == before
