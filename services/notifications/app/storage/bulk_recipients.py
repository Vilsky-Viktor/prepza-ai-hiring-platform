import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update

from app.constants.bulk import RecipientStatus
from app.models.bulk import BulkRecipient, BulkSend
from app.storage.db import Session

# Recipients still to send, of sends being sent.
OPEN = (
    BulkRecipient.status == RecipientStatus.PENDING,
    BulkSend.prepared_at.is_not(None),
    BulkSend.finished_at.is_(None),
)


async def pending(limit: int, skip: list[int]) -> list[tuple[int, uuid.UUID, str, str, str]]:
    """The next pending recipients, oldest send first, but those in `skip` (tried in this run):
    (row id, send id, user id, the send's kind, what it's about)."""
    query = (
        select(BulkRecipient.id, BulkSend.id, BulkRecipient.user_id, BulkSend.kind, BulkSend.about)
        .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
        .where(*OPEN, BulkRecipient.id.not_in(skip))
        .order_by(BulkSend.created_at, BulkRecipient.id)
        .limit(limit)
    )

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


@asynccontextmanager
async def claimed(row_id: int) -> AsyncIterator[BulkRecipient | None]:
    """The recipient's row while its email is sent, saved as the caller left it; None when it's
    no longer pending (sent, or its send stopped). No transaction stays open while the email
    goes: one bulk run works at a time (services/bulk.py), and Resend's idempotency key keeps a
    run cut off after sending from sending twice. An error inside leaves it as it was, pending,
    for the next run."""
    async with Session() as session:
        row = await session.scalar(
            select(BulkRecipient)
            .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
            .where(BulkRecipient.id == row_id, *OPEN)
        )

    yield row

    if row is None:
        return

    async with Session() as session:
        await session.execute(
            update(BulkRecipient)
            .where(BulkRecipient.id == row_id)
            .values(
                status=row.status, reason=row.reason, attempts=row.attempts, sent_at=row.sent_at
            )
        )
        await session.commit()


async def sent_since(since: datetime) -> int:
    """Bulk emails sent since then, against Resend's daily quota."""
    async with Session() as session:
        return await session.scalar(select(func.count()).where(BulkRecipient.sent_at >= since)) or 0


async def mark_unsubscribed(user_id: str, kind: str) -> None:
    """The user turned the `kind` setting off from an email: counted against the last campaign of
    that kind they got. Safe to repeat."""
    async with Session() as session:
        last = await session.scalar(
            select(BulkRecipient.id)
            .join(BulkSend, BulkSend.id == BulkRecipient.send_id)
            .where(
                BulkRecipient.user_id == user_id,
                BulkSend.kind == kind,
                BulkRecipient.sent_at.is_not(None),
            )
            .order_by(BulkRecipient.sent_at.desc())
            .limit(1)
        )

        if last is None:
            return

        await session.execute(
            update(BulkRecipient)
            .where(BulkRecipient.id == last, BulkRecipient.unsubscribed_at.is_(None))
            .values(unsubscribed_at=datetime.now(UTC))
        )
        await session.commit()


async def mark_complained(send_id: uuid.UUID, user_id: str) -> None:
    """Safe to repeat: Resend may send the web hook again."""
    async with Session() as session:
        await session.execute(
            update(BulkRecipient)
            .where(
                BulkRecipient.send_id == send_id,
                BulkRecipient.user_id == user_id,
                BulkRecipient.complained_at.is_(None),
            )
            .values(complained_at=datetime.now(UTC))
        )
        await session.commit()


async def is_recipient(send_id: uuid.UUID, user_id: str) -> bool:
    async with Session() as session:
        found = await session.scalar(
            select(BulkRecipient.id).where(
                BulkRecipient.send_id == send_id, BulkRecipient.user_id == user_id
            )
        )

    return found is not None


async def remove_user(user_id: str) -> None:
    """A deleted account's rows go."""
    async with Session() as session:
        await session.execute(delete(BulkRecipient).where(BulkRecipient.user_id == user_id))
        await session.commit()
