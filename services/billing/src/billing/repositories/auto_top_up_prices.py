from datetime import datetime

from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from billing.models.billing import AutoTopUp
from billing.models.outbox import OutboxEvent


def _of(owner_type: str, owner_id: str):
    return (AutoTopUp.owner_type == owner_type, AutoTopUp.owner_id == owner_id)


async def running(session: AsyncSession, after: tuple[str, str], limit: int) -> list[AutoTopUp]:
    """Running automatic top-ups (their card saved) after `after` (owner type and id), in that
    order, `limit` at most."""
    query = (
        select(AutoTopUp)
        .where(
            AutoTopUp.subscription_id.is_not(None),
            tuple_(AutoTopUp.owner_type, AutoTopUp.owner_id) > tuple_(*after),
        )
        .order_by(AutoTopUp.owner_type, AutoTopUp.owner_id)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def agree(
    session: AsyncSession, owner_type: str, owner_id: str, price: int, currency: str
) -> None:
    """`price` in `currency` is the one agreed from now on, with no new one announced: for a top-up
    set up before prices were kept, or after the company chose another currency."""
    await session.execute(
        update(AutoTopUp)
        .where(*_of(owner_type, owner_id))
        .values(price=price, price_currency=currency, next_price=None, next_price_from=None)
    )


async def announce(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    row: AutoTopUp,
    price: int,
    since: datetime,
    event: dict,
) -> bool:
    """A new price for the top-up, from `since`, with the notification that tells the company
    (`event`) in the same transaction. Only once per price, and only while the price agreed is
    still the one `row` was read with; whether this announced it."""
    changed = await session.scalar(
        update(AutoTopUp)
        .where(
            *_of(owner_type, owner_id),
            AutoTopUp.price == row.price,
            AutoTopUp.price_currency == row.price_currency,
            AutoTopUp.next_price.is_distinct_from(price),
        )
        .values(next_price=price, next_price_from=since)
        .returning(AutoTopUp.owner_id)
    )

    if changed is not None:
        outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, event)

    return changed is not None
