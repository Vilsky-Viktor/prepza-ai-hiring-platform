from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.db.db import delete_in_batches

from notifications.models.soft_bounces import SoftBounce


async def add(session: AsyncSession, address: str, email_id: str, since: datetime) -> int:
    """Counts a temporary bounce of the email `email_id` to the address (its hash), once however
    often it's reported; how many the address had since `since`, this one included."""
    await session.execute(
        insert(SoftBounce).values(address=address, email_id=email_id).on_conflict_do_nothing()
    )
    count = await session.scalar(
        select(func.count())
        .select_from(SoftBounce)
        .where(SoftBounce.address == address, SoftBounce.created_at >= since)
    )

    return count or 0


async def forget(sessions, before: datetime, until: float | None = None) -> None:
    """Bounces older than any window that counts them go, in batches (each its own transaction),
    none started after `until` (time.monotonic()); the next run deletes the rest."""
    await delete_in_batches(sessions, SoftBounce, SoftBounce.created_at < before, until=until)
