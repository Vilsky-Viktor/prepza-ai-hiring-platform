from datetime import datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE
from sqlalchemy import and_, case, delete, exists, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from billing.constants.products import AUTO_TOP_UP_COOLDOWN, AUTO_TOP_UP_UNCREDITED_WAIT
from billing.models.billing import AutoTopUp, Entry, Wallet


async def get(session: AsyncSession, owner_type: str, owner_id: str) -> AutoTopUp | None:
    return await session.get(AutoTopUp, (owner_type, owner_id))


async def save(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    product: str,
    threshold: int,
    buyer_id: str,
    price: int,
    currency: str,
    language: str = DEFAULT_LANGUAGE,
) -> AutoTopUp:
    """Sets what to buy and when. A running one keeps its subscription and the card it charges
    (a declined card isn't tried again sooner: its card is updated instead); one still waiting
    for its checkout waits for this person's, whoever turned it on before. Choosing another
    top-up agrees to its `price` now (in `currency`); keeping the same one keeps the price agreed
    and any new price announced. `language`, which names what each charge buys, is the buyer's:
    it changes only with the person whose card pays."""
    values = {"product": product, "threshold": threshold}
    upsert = insert(AutoTopUp).values(
        owner_type=owner_type,
        owner_id=owner_id,
        buyer_id=buyer_id,
        price=price,
        price_currency=currency,
        language=language,
        **values,
    )
    waiting = AutoTopUp.subscription_id.is_(None)
    buyers = or_(waiting, AutoTopUp.buyer_id == upsert.excluded.buyer_id)
    kept = AutoTopUp.product == upsert.excluded.product

    def unless_kept(column, chosen):
        return case((kept, column), else_=chosen)

    await session.execute(
        upsert.on_conflict_do_update(
            index_elements=["owner_type", "owner_id"],
            set_={
                **values,
                "buyer_id": case((waiting, upsert.excluded.buyer_id), else_=AutoTopUp.buyer_id),
                "language": case((buyers, upsert.excluded.language), else_=AutoTopUp.language),
                "price": unless_kept(AutoTopUp.price, upsert.excluded.price),
                "price_currency": unless_kept(
                    AutoTopUp.price_currency, upsert.excluded.price_currency
                ),
                "next_price": unless_kept(AutoTopUp.next_price, None),
                "next_price_from": unless_kept(AutoTopUp.next_price_from, None),
            },
        )
    )

    return await session.get(AutoTopUp, (owner_type, owner_id), populate_existing=True)


async def start(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    buyer_id: str,
    subscription_id: str,
    currency: str,
) -> bool:
    """Attaches the subscription, and its currency, from the checkout of whoever turned it on;
    once only. Paddle's two events for one checkout can arrive together, so finding it already
    attached counts as started too."""
    started = await session.scalar(
        update(AutoTopUp)
        .where(
            AutoTopUp.owner_type == owner_type,
            AutoTopUp.owner_id == owner_id,
            AutoTopUp.buyer_id == buyer_id,
            or_(
                AutoTopUp.subscription_id.is_(None),
                AutoTopUp.subscription_id == subscription_id,
            ),
        )
        .values(subscription_id=subscription_id, currency=currency)
        .returning(AutoTopUp.owner_id)
    )

    return started is not None


async def owner_of(session: AsyncSession, subscription_id: str) -> tuple[str, str] | None:
    """Whose wallet an automatic charge is for."""
    query = select(AutoTopUp.owner_type, AutoTopUp.owner_id).where(
        AutoTopUp.subscription_id == subscription_id
    )

    row = (await session.execute(query)).first()

    return (row.owner_type, row.owner_id) if row else None


async def claim_charge(
    session: AsyncSession, owner_type: str, owner_id: str, now: datetime
) -> AutoTopUp | None:
    """The running automatic top-up, if the available balance is under its threshold, it
    hasn't charged within the cooldown, it isn't paused and a declined card's retry is due
    (`retry_at`); marks it charged now. Atomic, so two requests at once charge once. The last
    charge's credits must have come first, else it waits AUTO_TOP_UP_UNCREDITED_WAIT."""
    credited = exists().where(
        Entry.owner_type == AutoTopUp.owner_type,
        Entry.owner_id == AutoTopUp.owner_id,
        Entry.automatic.is_(True),
        Entry.created_at >= AutoTopUp.charged_at,
    )
    query = (
        update(AutoTopUp)
        .where(
            AutoTopUp.owner_type == owner_type,
            AutoTopUp.owner_id == owner_id,
            AutoTopUp.subscription_id.is_not(None),
            or_(
                AutoTopUp.charged_at.is_(None),
                # Declined: the retry wait below applies.
                AutoTopUp.failed_at >= AutoTopUp.charged_at,
                and_(AutoTopUp.charged_at < now - AUTO_TOP_UP_COOLDOWN, credited),
                AutoTopUp.charged_at < now - AUTO_TOP_UP_UNCREDITED_WAIT,
            ),
            AutoTopUp.paused_at.is_(None),
            or_(AutoTopUp.retry_at.is_(None), AutoTopUp.retry_at <= now),
            Wallet.owner_type == AutoTopUp.owner_type,
            Wallet.owner_id == AutoTopUp.owner_id,
            Wallet.balance - Wallet.reserved < AutoTopUp.threshold,
        )
        .values(charged_at=now)
        .returning(AutoTopUp)
    )

    row = await session.scalar(query)

    return row


async def remove(
    session: AsyncSession, owner_type: str, owner_id: str, buyer_id: str | None = None
) -> str | None:
    """Turns it off, or only when `buyer_id` turned it on; the subscription to cancel, if it had
    started."""
    query = delete(AutoTopUp).where(
        AutoTopUp.owner_type == owner_type, AutoTopUp.owner_id == owner_id
    )

    if buyer_id is not None:
        query = query.where(AutoTopUp.buyer_id == buyer_id)

    subscription_id = await session.scalar(query.returning(AutoTopUp.subscription_id))

    return subscription_id


async def of_buyer(session: AsyncSession, buyer_id: str) -> list[AutoTopUp]:
    """The automatic top-ups this person turned on, paid with their card once started."""
    return list(await session.scalars(select(AutoTopUp).where(AutoTopUp.buyer_id == buyer_id)))


async def remove_for_buyer(session: AsyncSession, buyer_id: str) -> list[str]:
    """Turns off every automatic top-up paid with this person's card; the subscriptions to
    cancel."""
    rows = await session.scalars(
        delete(AutoTopUp).where(AutoTopUp.buyer_id == buyer_id).returning(AutoTopUp.subscription_id)
    )
    subscriptions = [row for row in rows if row]

    return subscriptions


async def set_currency(session: AsyncSession, subscription_id: str, currency: str) -> None:
    """The currency Paddle now charges the subscription in."""
    await session.execute(
        update(AutoTopUp)
        .where(AutoTopUp.subscription_id == subscription_id)
        .values(currency=currency)
    )


async def remove_subscription(session: AsyncSession, subscription_id: str) -> None:
    """Paddle ended the subscription: automatic top-up is off."""
    await session.execute(delete(AutoTopUp).where(AutoTopUp.subscription_id == subscription_id))
