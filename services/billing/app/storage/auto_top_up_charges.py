from datetime import datetime

from sqlalchemy import case, update

from app.constants.declines import AUTO_TOP_UP_RETRY_WAITS
from app.models.billing import AutoTopUp
from app.storage.db import Session


def _of(owner_type: str, owner_id: str):
    return (AutoTopUp.owner_type == owner_type, AutoTopUp.owner_id == owner_id)


async def declined(owner_type: str, owner_id: str, now: datetime) -> bool:
    """The card declined the charge: one more decline in a row, the next try waits the retry
    wait of that many (AUTO_TOP_UP_RETRY_WAITS), and one past the last pauses it. Whether this
    paused it."""
    count = AutoTopUp.declines + 1
    waits = {index: now + wait for index, wait in enumerate(AUTO_TOP_UP_RETRY_WAITS, start=1)}
    over = count > len(AUTO_TOP_UP_RETRY_WAITS)

    async with Session() as session:
        paused = await session.scalar(
            update(AutoTopUp)
            .where(*_of(owner_type, owner_id), AutoTopUp.paused_at.is_(None))
            .values(
                declines=count,
                failed_at=now,
                retry_at=case(waits, value=count, else_=None),
                paused_at=case((over, now), else_=None),
            )
            .returning(AutoTopUp.paused_at)
        )
        await session.commit()

    return paused is not None


async def pause(owner_type: str, owner_id: str, now: datetime) -> bool:
    """A decline that can't pass later: no charge until the card is updated. Whether this paused
    it (not paused already)."""
    async with Session() as session:
        paused = await session.scalar(
            update(AutoTopUp)
            .where(*_of(owner_type, owner_id), AutoTopUp.paused_at.is_(None))
            .values(paused_at=now, retry_at=None)
            .returning(AutoTopUp.owner_id)
        )
        await session.commit()

    return paused is not None


async def charged(owner_type: str, owner_id: str) -> None:
    """A charge went through: no declines in a row."""
    async with Session() as session:
        await session.execute(
            update(AutoTopUp).where(*_of(owner_type, owner_id)).values(declines=0, retry_at=None)
        )
        await session.commit()


async def resume(subscription_id: str, card_saved_at: datetime) -> tuple[str, str] | None:
    """The subscription's card was updated at `card_saved_at`: a pause from before then ends and
    the declines start over. Whose it was, or None when it wasn't paused then (a repeated web
    hook, or one paused again since)."""
    async with Session() as session:
        row = (
            await session.execute(
                update(AutoTopUp)
                .where(
                    AutoTopUp.subscription_id == subscription_id,
                    AutoTopUp.paused_at <= card_saved_at,
                )
                .values(paused_at=None, declines=0, retry_at=None, failed_at=None)
                .returning(AutoTopUp.owner_type, AutoTopUp.owner_id)
            )
        ).first()
        await session.commit()

    return (row.owner_type, row.owner_id) if row else None
