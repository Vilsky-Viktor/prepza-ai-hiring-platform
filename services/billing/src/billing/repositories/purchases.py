from datetime import datetime

from prepza_common.events.audit_actions import AuditAction
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from billing.constants.credits import Reason
from billing.constants.products import OwnerType
from billing.models.billing import Entry, Purchase
from billing.repositories import company_actions
from billing.repositories.events import save
from billing.repositories.ledger import add, ensure


async def grant(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    credits: int,
    quantity: int,
    transaction_id: str,
    product: str,
    buyer_id: str | None,
    total: str,
    currency: str,
    now: datetime,
    automatic: bool = False,
    events: list[tuple[str, dict]] = (),
) -> bool:
    """Adds a paid top-up once per product of a transaction, however often Paddle retries, with
    `events` (type, data) for the outbox in the same transaction. `credits` is what the whole
    line buys; `quantity` is kept for the accounts."""
    new = await session.scalar(
        insert(Purchase)
        .values(
            transaction_id=transaction_id,
            product=product,
            quantity=quantity,
            owner_type=owner_type,
            owner_id=owner_id,
            buyer_id=buyer_id,
            total_minor=int(total),
            currency=currency,
            created_at=now,
        )
        .on_conflict_do_nothing()
        .returning(Purchase.id)
    )

    if new is None:
        return False

    await ensure(session, owner_type, owner_id)
    await add(
        session,
        owner_type,
        owner_id,
        credits,
        f"{transaction_id}:{product}",
        Reason.TOPUP,
        total,
        currency,
        automatic,
    )
    save(session, events)

    return True


def log_top_up(session: AsyncSession, company_id: str, buyer_id: str) -> None:
    """The member's top-up, for the company's action log, through the outbox."""
    company_actions.log(session, company_id, buyer_id, AuditAction.TOP_UP_PAID)


async def for_transaction(
    session: AsyncSession, transaction_id: str
) -> tuple[str, str, int, int] | None:
    """Whose wallet a transaction topped up, the credits it bought, and what was paid."""
    rows = list(
        await session.scalars(select(Purchase).where(Purchase.transaction_id == transaction_id))
    )

    if not rows:
        return None

    granted = await session.scalar(
        select(func.coalesce(func.sum(Entry.amount), 0)).where(
            Entry.key.in_([f"{transaction_id}:{row.product}" for row in rows])
        )
    )
    first = rows[0]

    return first.owner_type, first.owner_id, granted, first.total_minor


async def take_back(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    amount: int,
    transaction_id: str,
    adjustment_id: str,
    reason: str,
    total: str | None = None,
    currency: str | None = None,
    events: list[tuple[str, dict]] = (),
) -> int:
    """Moves an adjustment's credits once, whatever the balance (a refund or chargeback may leave
    it negative), with `events` for the outbox when it moves them, and returns how many credits
    the transaction's adjustments have taken back so far, less what reversals returned. The
    transaction's lines are locked, so adjustments of one transaction arriving together are
    counted one after the other."""
    prefix = f"adjustment:{transaction_id}:"
    await session.execute(
        select(Purchase.id)
        .where(Purchase.transaction_id == transaction_id)
        .order_by(Purchase.id)
        .with_for_update()
    )
    # Adjustments counted before their keys carried the transaction aren't counted again.
    counted = await session.scalar(
        select(Entry.id).where(Entry.key == f"adjustment:{adjustment_id}")
    )

    if counted is None:
        await ensure(session, owner_type, owner_id)
        moved = await add(
            session, owner_type, owner_id, amount, prefix + adjustment_id, reason, total, currency
        )

        # A repeated adjustment moves nothing, so it tells nobody again.
        if moved:
            save(session, events)

    return await session.scalar(
        select(func.coalesce(-func.sum(Entry.amount), 0)).where(
            Entry.key.startswith(prefix, autoescape=True)
        )
    )


async def credited(session: AsyncSession, transaction_ids: list[str]) -> set[str]:
    """Which of these transactions have added their credits."""
    query = select(Purchase.transaction_id).where(Purchase.transaction_id.in_(transaction_ids))

    return set(await session.scalars(query))


async def counted(session: AsyncSession, adjustments: list[tuple[str, str]]) -> set[str]:
    """Which of these adjustments, as (transaction id, adjustment id), have moved credits."""
    keys = {
        f"adjustment:{transaction_id}:{adjustment_id}": adjustment_id
        for transaction_id, adjustment_id in adjustments
    }
    query = select(Entry.key).where(Entry.key.in_(list(keys)))

    return {keys[key] for key in await session.scalars(query)}


async def paid(session: AsyncSession, owner_type: str, owner_id: str) -> bool:
    """Whether this wallet was ever topped up."""
    query = select(Purchase.id).where(
        Purchase.owner_type == owner_type, Purchase.owner_id == owner_id
    )

    return await session.scalar(query.limit(1)) is not None


async def owns(session: AsyncSession, owner_type: str, owner_id: str, transaction_id: str) -> bool:
    """Whether the transaction topped up this wallet."""
    query = select(Purchase.id).where(
        Purchase.transaction_id == transaction_id,
        Purchase.owner_type == owner_type,
        Purchase.owner_id == owner_id,
    )

    return await session.scalar(query.limit(1)) is not None


async def purchases_of(session: AsyncSession, user_id: str) -> list[Purchase]:
    query = select(Purchase).where(Purchase.buyer_id == user_id).order_by(Purchase.created_at)

    return list(await session.scalars(query))


async def bought_by(session: AsyncSession, user_id: str, limit: int) -> list:
    """The company top-ups the user paid for, one per transaction, newest first: each
    transaction's lines share its total."""
    query = (
        select(
            Purchase.transaction_id,
            Purchase.owner_id,
            Purchase.total_minor.label("total"),
            Purchase.currency,
            func.min(Purchase.created_at).label("created_at"),
        )
        .where(Purchase.buyer_id == user_id, Purchase.owner_type == OwnerType.COMPANY)
        .group_by(
            Purchase.transaction_id, Purchase.owner_id, Purchase.total_minor, Purchase.currency
        )
        .order_by(func.min(Purchase.created_at).desc())
        .limit(limit)
    )

    return list(await session.execute(query))


async def forget_buyer(session: AsyncSession, user_id: str) -> None:
    """Purchases stay with their companies for the accounts, without who paid."""
    await session.execute(
        update(Purchase).where(Purchase.buyer_id == user_id).values(buyer_id=None)
    )
