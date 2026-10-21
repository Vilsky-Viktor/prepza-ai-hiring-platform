from datetime import datetime

from prepza_common import audit
from prepza_common.audit_actions import AuditAction, TargetKind
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.credits import Reason
from app.constants.products import OwnerType
from app.models.billing import Entry, Hold, Purchase, Wallet
from app.models.outbox import OutboxEvent
from app.storage import referrals
from app.storage.db import Session
from app.storage.ledger import add, ensure


async def grant(
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
) -> bool:
    """Adds a paid top-up once per product of a transaction, however often Paddle retries.
    `credits` is what the whole line buys; `quantity` is kept for the accounts."""
    async with Session() as session:
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
            await session.commit()

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

        # A member's own top-up goes to the company's action log; an automatic one isn't theirs.
        if owner_type == OwnerType.COMPANY and buyer_id and not automatic:
            audit.add(
                session,
                OutboxEvent,
                owner_id,
                buyer_id,
                AuditAction.TOP_UP_PAID,
                TargetKind.COMPANY,
                owner_id,
            )

        await session.commit()

        return True


async def for_transaction(transaction_id: str) -> tuple[str, str, int, int] | None:
    """Whose wallet a transaction topped up, the credits it bought, and what was paid."""
    async with Session() as session:
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
    owner_type: str,
    owner_id: str,
    amount: int,
    transaction_id: str,
    adjustment_id: str,
    reason: str,
    total: str | None = None,
    currency: str | None = None,
) -> int:
    """Moves an adjustment's credits once, whatever the balance (a refund or chargeback may leave
    it negative), and returns how many credits the transaction's adjustments have taken back so
    far, less what reversals returned. The transaction's lines are locked, so adjustments of one
    transaction arriving together are counted one after the other."""
    prefix = f"adjustment:{transaction_id}:"

    async with Session() as session:
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
            await add(
                session,
                owner_type,
                owner_id,
                amount,
                prefix + adjustment_id,
                reason,
                total,
                currency,
            )

        taken = await session.scalar(
            select(func.coalesce(-func.sum(Entry.amount), 0)).where(
                Entry.key.startswith(prefix, autoescape=True)
            )
        )
        await session.commit()

    return taken


async def credited(transaction_ids: list[str]) -> set[str]:
    """Which of these transactions have added their credits."""
    query = select(Purchase.transaction_id).where(Purchase.transaction_id.in_(transaction_ids))

    async with Session() as session:
        return set(await session.scalars(query))


async def counted(adjustments: list[tuple[str, str]]) -> set[str]:
    """Which of these adjustments, as (transaction id, adjustment id), have moved credits."""
    keys = {
        f"adjustment:{transaction_id}:{adjustment_id}": adjustment_id
        for transaction_id, adjustment_id in adjustments
    }
    query = select(Entry.key).where(Entry.key.in_(list(keys)))

    async with Session() as session:
        return {keys[key] for key in await session.scalars(query)}


async def paid(owner_type: str, owner_id: str) -> bool:
    """Whether this wallet was ever topped up."""
    query = select(Purchase.id).where(
        Purchase.owner_type == owner_type, Purchase.owner_id == owner_id
    )

    async with Session() as session:
        return await session.scalar(query.limit(1)) is not None


async def owns(owner_type: str, owner_id: str, transaction_id: str) -> bool:
    """Whether the transaction topped up this wallet."""
    query = select(Purchase.id).where(
        Purchase.transaction_id == transaction_id,
        Purchase.owner_type == owner_type,
        Purchase.owner_id == owner_id,
    )

    async with Session() as session:
        return await session.scalar(query.limit(1)) is not None


async def purchases_of(user_id: str) -> list[Purchase]:
    query = select(Purchase).where(Purchase.buyer_id == user_id).order_by(Purchase.created_at)

    async with Session() as session:
        return list(await session.scalars(query))


async def bought_by(user_id: str, limit: int) -> list:
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

    async with Session() as session:
        return list(await session.execute(query))


async def forget_buyer(user_id: str) -> None:
    """Purchases stay with their companies for the accounts, without who paid."""
    async with Session() as session:
        await session.execute(
            update(Purchase).where(Purchase.buyer_id == user_id).values(buyer_id=None)
        )
        await session.commit()


async def delete_company(company_id: str) -> None:
    """A deleted company's wallet, holds and history; its purchases stay for the accounts."""
    is_company = {"owner_type": OwnerType.COMPANY, "owner_id": company_id}

    async with Session() as session:
        await session.execute(delete(Wallet).filter_by(**is_company))
        await session.execute(delete(Hold).filter_by(**is_company))
        await session.execute(delete(Entry).filter_by(**is_company))
        await referrals.forget(session, OwnerType.COMPANY, company_id)
        await session.commit()
