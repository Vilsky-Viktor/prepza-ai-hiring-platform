from datetime import datetime

from prepza_common.db.db import delete_in_batches
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from notifications.core.db import Session
from notifications.models.soft_bounces import SoftBounce


async def add(address: str, email_id: str, since: datetime) -> int:
    """Counts a temporary bounce of the email `email_id` to the address (its hash), once however
    often it's reported; how many the address had since `since`, this one included."""
    async with Session() as session:
        await session.execute(
            insert(SoftBounce).values(address=address, email_id=email_id).on_conflict_do_nothing()
        )
        await session.commit()
        count = await session.scalar(
            select(func.count())
            .select_from(SoftBounce)
            .where(SoftBounce.address == address, SoftBounce.created_at >= since)
        )

    return count or 0


async def forget(before: datetime, until: float | None = None) -> None:
    """Bounces older than any window that counts them go, in batches, none started after `until`
    (time.monotonic()); the next run deletes the rest."""
    await delete_in_batches(Session, SoftBounce, SoftBounce.created_at < before, until=until)
