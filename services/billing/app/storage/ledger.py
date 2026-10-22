from sqlalchemy import exists, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.constants.credits import LOW_BALANCE, WELCOME_COMPANY, WELCOME_GIFT, HoldStatus, Reason
from app.constants.products import OwnerType
from app.helpers.gifts import gift_key, legacy_gift_key
from app.models.billing import AutoTopUp, Entry, Gift, Hold, Wallet
from app.storage.db import Session


async def wallet(owner_type: str, owner_id: str) -> Wallet:
    """The wallet, created empty the first time."""
    async with Session() as session:
        await ensure(session, owner_type, owner_id)
        await session.commit()

        return await session.get(Wallet, (owner_type, owner_id))


async def wallets(owner_type: str, owner_ids: list[str]) -> dict[str, Wallet]:
    """Existing wallets by owner id; owners without one have nothing yet."""
    query = select(Wallet).where(Wallet.owner_type == owner_type, Wallet.owner_id.in_(owner_ids))

    async with Session() as session:
        return {row.owner_id: row for row in await session.scalars(query)}


async def running_low(
    owner_type: str, owner_ids: list[str] | None = None, after: str = "", limit: int | None = None
) -> list[Wallet]:
    """Wallets running low (as helpers/wallets.py tells it) that no automatic top-up refills;
    with `owner_ids`, only theirs; else up to `limit` by owner id, those after `after`."""
    refilled = exists().where(
        AutoTopUp.owner_type == Wallet.owner_type,
        AutoTopUp.owner_id == Wallet.owner_id,
        AutoTopUp.subscription_id.is_not(None),
    )
    query = select(Wallet).where(
        Wallet.owner_type == owner_type, Wallet.balance - Wallet.reserved < LOW_BALANCE, ~refilled
    )

    if owner_ids is not None:
        query = query.where(Wallet.owner_id.in_(owner_ids))
    else:
        query = query.where(Wallet.owner_id > after).order_by(Wallet.owner_id).limit(limit)

    async with Session() as session:
        return list(await session.scalars(query))


async def welcome_company(company_id: str, owner_email: str) -> bool:
    """Creates the company's wallet with the welcome credits, once per owner's email: a person's
    first company. Deleting and creating one again doesn't repeat it. True when this company got
    the gift, now or in an earlier try whose answer was lost."""
    async with Session() as session:
        await ensure(session, OwnerType.COMPANY, company_id)
        given_before = await session.get(
            Gift, legacy_gift_key(WELCOME_GIFT, owner_email, settings.person_hash_key)
        )
        new = await session.scalar(
            insert(Gift)
            .values(key=gift_key(WELCOME_GIFT, owner_email, settings.person_hash_key))
            .on_conflict_do_nothing()
            .returning(Gift.key)
        )
        # Given under the key before inbox_of: not again.
        new = new if given_before is None else None

        if new:
            await add(
                session,
                OwnerType.COMPANY,
                company_id,
                WELCOME_COMPANY,
                f"welcome:{company_id}",
                Reason.WELCOME,
            )

        welcomed = await session.scalar(
            select(Entry.key).where(Entry.key == f"welcome:{company_id}")
        )
        await session.commit()

        return welcomed is not None


async def reserve(owner_type: str, owner_id: str, amount: int, key: str, reason: str) -> bool:
    """Sets credits aside. Repeating the same key does it once; a released hold can be taken
    again. False when the available balance is too low."""
    async with Session() as session:
        await ensure(session, owner_type, owner_id)
        # The wallet's lock comes first, so two requests for the same hold can't both add it.
        row = await session.get(Wallet, (owner_type, owner_id), with_for_update=True)
        hold = await session.get(Hold, key)

        if hold is not None and hold.status != HoldStatus.RELEASED:
            await session.commit()

            return True

        if row.balance - row.reserved < amount:
            await session.commit()

            return False

        row.reserved += amount
        # A new hold, or the released one with this key opened again.
        await session.merge(
            Hold(
                key=key,
                owner_type=owner_type,
                owner_id=owner_id,
                amount=amount,
                reason=reason,
                status=HoldStatus.OPEN,
            )
        )
        await session.commit()

        return True


async def charge(key: str) -> None:
    """Takes the credits a hold set aside. Safe to repeat; does nothing without an open hold."""
    async with Session() as session:
        hold = await open_hold(session, key)

        if hold is None:
            return

        await session.execute(
            update(Wallet)
            .where(Wallet.owner_type == hold.owner_type, Wallet.owner_id == hold.owner_id)
            .values(reserved=Wallet.reserved - hold.amount)
        )
        await add(session, hold.owner_type, hold.owner_id, -hold.amount, key, hold.reason)
        hold.status = HoldStatus.CHARGED
        await session.commit()


async def release(key: str) -> None:
    """Gives back credits a hold set aside. Safe to repeat."""
    async with Session() as session:
        hold = await open_hold(session, key)

        if hold is None:
            return

        await session.execute(
            update(Wallet)
            .where(Wallet.owner_type == hold.owner_type, Wallet.owner_id == hold.owner_id)
            .values(reserved=Wallet.reserved - hold.amount)
        )
        hold.status = HoldStatus.RELEASED
        await session.commit()


async def hold_status(key: str) -> str | None:
    """Whether the hold is open, charged or released; None when there's none."""
    async with Session() as session:
        return await session.scalar(select(Hold.status).where(Hold.key == key))


async def open_hold(session: AsyncSession, key: str) -> Hold | None:
    """The open hold, locked. Its wallet is locked first, as everywhere else (reserve, deleting
    a company), so two transactions never wait on each other's lock."""
    hold = await session.get(Hold, key)

    if hold is None:
        return None

    await session.get(Wallet, (hold.owner_type, hold.owner_id), with_for_update=True)
    hold = await session.get(Hold, key, with_for_update=True, populate_existing=True)

    return hold if hold is not None and hold.status == HoldStatus.OPEN else None


async def ensure(session: AsyncSession, owner_type: str, owner_id: str) -> None:
    """Creates the wallet, empty; the welcome gift comes from welcome()."""
    await session.execute(
        insert(Wallet)
        .values(owner_type=owner_type, owner_id=owner_id, balance=0, reserved=0)
        .on_conflict_do_nothing()
    )


async def add(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    amount: int,
    key: str,
    reason: str,
    total: str | None = None,
    currency: str | None = None,
    automatic: bool = False,
    note: str | None = None,
) -> bool:
    """Records one movement and applies it to the balance, once per key; a top-up, refund or
    chargeback with the money it moved, an adjustment with its note."""
    new = await session.scalar(
        insert(Entry)
        .values(
            key=key,
            owner_type=owner_type,
            owner_id=owner_id,
            amount=amount,
            reason=reason,
            total_minor=int(total) if total is not None else None,
            currency=currency,
            automatic=automatic,
            note=note,
        )
        .on_conflict_do_nothing()
        .returning(Entry.id)
    )

    if new is None:
        return False

    await session.execute(
        update(Wallet)
        .where(Wallet.owner_type == owner_type, Wallet.owner_id == owner_id)
        .values(balance=Wallet.balance + amount)
    )

    return True


async def adjust(owner_type: str, owner_id: str, amount: int, key: str, note: str) -> bool:
    """A superadmin's adjustment, once per key; False, changing nothing, when it would take the
    available balance (not counting credits set aside for candidates) below zero."""
    async with Session() as session, session.begin():
        await ensure(session, owner_type, owner_id)
        wallet = await session.scalar(
            select(Wallet)
            .where(Wallet.owner_type == owner_type, Wallet.owner_id == owner_id)
            .with_for_update()
        )

        if wallet.balance - wallet.reserved + amount < 0:
            return False

        await add(session, owner_type, owner_id, amount, key, Reason.ADJUSTMENT, note=note)

    return True
