"""A company's wallet: its balance, the welcome credits it starts with and a superadmin's
adjustments."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from billing.config import settings
from billing.constants.credits import (
    ADJUSTMENT_BELOW_ZERO,
    ADJUSTMENT_ZERO,
    WELCOME_COMPANY,
    WELCOME_GIFT,
    Reason,
)
from billing.constants.currencies import ChoiceOwner
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.helpers.gifts import gift_key, legacy_gift_key
from billing.helpers.wallets import balance_out
from billing.repositories import ledger, referrals
from billing.schemas.billing import AdjustmentIn, BalanceOut, WelcomeIn
from billing.services.currencies import saved_in


async def credits(owner_type: str, owner_id: str) -> BalanceOut:
    """The balance, its wallet made empty the first time."""
    async with Session.begin() as session:
        return balance_out(await ledger.wallet(session, owner_type, owner_id))


async def welcome_gift(session: AsyncSession, company_id: str, owner_email: str) -> bool:
    """Creates the company's wallet with the welcome credits, once per owner's email: a person's
    first company. Deleting and creating one again doesn't repeat it. True when this company got
    the gift, now or in an earlier try whose answer was lost."""
    key = settings.person_hash_key
    entry = f"welcome:{company_id}"
    await ledger.ensure(session, OwnerType.COMPANY, company_id)
    new = await ledger.claim_gift(
        session,
        gift_key(WELCOME_GIFT, owner_email, key),
        # Given under the key before inbox_of: not again.
        legacy_gift_key(WELCOME_GIFT, owner_email, key),
    )

    if new:
        await ledger.add(
            session, OwnerType.COMPANY, company_id, WELCOME_COMPANY, entry, Reason.WELCOME
        )

    return await ledger.has_entry(session, entry)


async def welcome(company_id: str, body: WelcomeIn) -> None:
    """The company's wallet, in one save. The welcome credits come once per owner's email; a
    company new in that sense can be referred by another, unrelated one."""
    async with Session.begin() as session:
        if await welcome_gift(session, company_id, body.owner_email) and body.referral:
            await referrals.record(
                session, body.referral, OwnerType.COMPANY, company_id, body.related
            )

        # It pays in the currency of the country it's created in, until changed.
        await saved_in(session, ChoiceOwner.COMPANY, company_id, body.country)


async def adjust(company_id: str, body: AdjustmentIn) -> None:
    """A superadmin adds or removes credits. Safe to repeat with the same key; refused when it
    would take the available balance below zero."""
    if body.amount == 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ADJUSTMENT_ZERO)

    note = body.note.strip()
    key = f"adjustment:{body.key}"

    async with Session.begin() as session:
        adjusted = await ledger.adjust(
            session, OwnerType.COMPANY, company_id, body.amount, key, note
        )

    if not adjusted:
        raise HTTPException(status.HTTP_409_CONFLICT, ADJUSTMENT_BELOW_ZERO)
