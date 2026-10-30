import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.constants.bulk import RecipientStatus
from notifications.models.bulk import BulkRecipient, BulkSend

# Recipients still to send, of sends being sent.
OPEN = (
    BulkRecipient.status == RecipientStatus.PENDING,
    BulkSend.prepared_at.is_not(None),
    BulkSend.finished_at.is_(None),
)


async def pending(
    session: AsyncSession, limit: int, skip: list[int]
) -> list[tuple[int, uuid.UUID, str, str, str]]:
    """The next pending recipients, oldest send first, but those in `skip` (tried in this run):
    (row id, send id, user id, the send's kind, what it's about)."""
    query = (
        select(BulkRecipient.id, BulkSend.id, BulkRecipient.user_id, BulkSend.kind, BulkSend.about)
        .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
        .where(*OPEN, BulkRecipient.id.not_in(skip))
        .order_by(BulkSend.created_at, BulkRecipient.id)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def still_pending(session: AsyncSession, row_id: int) -> BulkRecipient | None:
    """The recipient's row while it's pending and its send is being sent; None when it was sent
    or its send stopped."""
    return await session.scalar(
        select(BulkRecipient)
        .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
        .where(BulkRecipient.id == row_id, *OPEN)
    )


async def save(session: AsyncSession, row: BulkRecipient) -> None:
    """The row's outcome as the sender left it: its status, reason, attempts and when it was
    sent."""
    await session.execute(
        update(BulkRecipient)
        .where(BulkRecipient.id == row.id)
        .values(status=row.status, reason=row.reason, attempts=row.attempts, sent_at=row.sent_at)
    )


async def sent_since(session: AsyncSession, since: datetime) -> int:
    """Bulk emails sent since then, against Resend's daily quota."""
    return await session.scalar(select(func.count()).where(BulkRecipient.sent_at >= since)) or 0


async def mark_unsubscribed(session: AsyncSession, user_id: str, kind: str) -> None:
    """The user turned the `kind` setting off from an email: counted against the last campaign of
    that kind they got. Safe to repeat."""
    last = (
        select(BulkRecipient.id)
        .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
        .where(
            BulkRecipient.user_id == user_id,
            BulkSend.kind == kind,
            BulkRecipient.sent_at.is_not(None),
        )
        .order_by(BulkRecipient.sent_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    await session.execute(
        update(BulkRecipient)
        .where(BulkRecipient.id == last, BulkRecipient.unsubscribed_at.is_(None))
        .values(unsubscribed_at=datetime.now(UTC))
    )


async def mark_complained(session: AsyncSession, send_id: uuid.UUID, user_id: str) -> None:
    """Safe to repeat: Resend may send the web hook again."""
    await session.execute(
        update(BulkRecipient)
        .where(
            BulkRecipient.send_id == send_id,
            BulkRecipient.user_id == user_id,
            BulkRecipient.complained_at.is_(None),
        )
        .values(complained_at=datetime.now(UTC))
    )


async def is_recipient(session: AsyncSession, send_id: uuid.UUID, user_id: str) -> bool:
    found = await session.scalar(
        select(BulkRecipient.id).where(
            BulkRecipient.send_id == send_id, BulkRecipient.user_id == user_id
        )
    )

    return found is not None


async def remove_user(session: AsyncSession, user_id: str) -> None:
    """A deleted account's rows go."""
    await session.execute(delete(BulkRecipient).where(BulkRecipient.user_id == user_id))


async def of_user(session: AsyncSession, user_id: str) -> list[tuple[BulkSend, BulkRecipient]]:
    """The notices and campaigns the user was among the recipients of, for their export."""
    rows = await session.execute(
        select(BulkSend, BulkRecipient)
        .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
        .where(BulkRecipient.user_id == user_id)
        .order_by(BulkSend.created_at.desc())
    )

    return [tuple(row) for row in rows]
