from sqlalchemy import delete, exists, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.db.db import delete_in_batches

from billing.constants.credits import LOW_BALANCE, HoldStatus, Reason
from billing.constants.products import OwnerType
from billing.models.billing import AutoTopUp, Entry, Gift, Hold, Wallet


async def wallet(session: AsyncSession, owner_type: str, owner_id: str) -> Wallet:
    """The wallet, created empty the first time."""
    await ensure(session, owner_type, owner_id)

    return await session.get(Wallet, (owner_type, owner_id), populate_existing=True)


async def wallets(
    session: AsyncSession, owner_type: str, owner_ids: list[str]
) -> dict[str, Wallet]:
    """Existing wallets by owner id; owners without one have nothing yet."""
    query = select(Wallet).where(Wallet.owner_type == owner_type, Wallet.owner_id.in_(owner_ids))

    return {row.owner_id: row for row in await session.scalars(query)}


async def running_low(
    session: AsyncSession,
    owner_type: str,
    owner_ids: list[str] | None = None,
    after: str = "",
    limit: int | None = None,
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

    return list(await session.scalars(query))


async def claim_gift(session: AsyncSession, key: str, legacy_key: str) -> bool:
    """Notes a gift given under `key`, once: False when it was given before, under this key or
    under `legacy_key`, the key of the same gift before inbox_of."""
    given_before = await session.get(Gift, legacy_key)
    new = await session.scalar(
        insert(Gift).values(key=key).on_conflict_do_nothing().returning(Gift.key)
    )

    return new is not None and given_before is None


async def has_entry(session: AsyncSession, key: str) -> bool:
    return await session.scalar(select(Entry.key).where(Entry.key == key)) is not None


async def reserve(
    session: AsyncSession, owner_type: str, owner_id: str, amount: int, key: str, reason: str
) -> bool:
    """Sets credits aside. Repeating the same key does it once; a released hold can be taken
    again. False when the available balance is too low."""
    await ensure(session, owner_type, owner_id)
    # The wallet's lock comes first, so two requests for the same hold can't both add it.
    row = await session.get(
        Wallet, (owner_type, owner_id), with_for_update=True, populate_existing=True
    )
    hold = await session.get(Hold, key)

    if hold is not None and hold.status != HoldStatus.RELEASED:
        return True

    if row.balance - row.reserved < amount:
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

    return True


async def charge(session: AsyncSession, key: str) -> None:
    """Takes the credits a hold set aside. Safe to repeat; does nothing without an open hold."""
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


async def release(session: AsyncSession, key: str) -> None:
    """Gives back credits a hold set aside. Safe to repeat."""
    hold = await open_hold(session, key)

    if hold is None:
        return

    await session.execute(
        update(Wallet)
        .where(Wallet.owner_type == hold.owner_type, Wallet.owner_id == hold.owner_id)
        .values(reserved=Wallet.reserved - hold.amount)
    )
    hold.status = HoldStatus.RELEASED


async def hold_status(session: AsyncSession, key: str) -> str | None:
    """Whether the hold is open, charged or released; None when there's none."""
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
    """Creates the wallet, empty; the welcome gift comes from services/wallets.py."""
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


async def adjust(
    session: AsyncSession, owner_type: str, owner_id: str, amount: int, key: str, note: str
) -> bool:
    """A superadmin's adjustment, once per key; False, changing nothing, when it would take the
    available balance (not counting credits set aside for candidates) below zero."""
    await ensure(session, owner_type, owner_id)
    wallet = await session.scalar(
        select(Wallet)
        .where(Wallet.owner_type == owner_type, Wallet.owner_id == owner_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if wallet.balance - wallet.reserved + amount < 0:
        return False

    await add(session, owner_type, owner_id, amount, key, Reason.ADJUSTMENT, note=note)

    return True


async def delete_history(sessions, company_id: str) -> None:
    """A deleted company's holds and history, a batch at a time, each batch its own transaction
    from the factory `sessions`. Cut off midway, it goes on when run again."""
    for model in (Hold, Entry):
        owned = (model.owner_type == OwnerType.COMPANY, model.owner_id == company_id)
        await delete_in_batches(sessions, model, *owned)


async def delete_wallet(session: AsyncSession, company_id: str) -> None:
    await session.execute(
        delete(Wallet).filter_by(owner_type=OwnerType.COMPANY, owner_id=company_id)
    )
