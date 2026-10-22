import uuid
from datetime import UTC, datetime

from prepza_common.constants import DELETE_BATCH
from sqlalchemy import case, exists, func, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.bulk import RecipientStatus, SkipReason
from app.models.bulk import BulkRecipient, BulkSend
from app.storage.db import Session

# Recipients are inserted this many at a time.
INSERT_CHUNK = 1000


async def start(kind: str, about: str, asked_by: str) -> uuid.UUID | None:
    """A new send; None when this one was started already (two clicks at once too)."""
    async with Session() as session:
        send_id = await session.scalar(
            insert(BulkSend)
            .values(id=uuid.uuid4(), kind=kind, about=about, asked_by=asked_by)
            .on_conflict_do_nothing()
            .returning(BulkSend.id)
        )
        await session.commit()

    return send_id


async def of_kinds(kinds: list[str]) -> list[BulkSend]:
    async with Session() as session:
        return list(await session.scalars(select(BulkSend).where(BulkSend.kind.in_(kinds))))


async def get(kind: str, about: str) -> BulkSend | None:
    async with Session() as session:
        return await session.scalar(
            select(BulkSend).where(BulkSend.kind == kind, BulkSend.about == about)
        )


async def of_campaigns(kind_abouts: list[tuple[str, str]]) -> dict[tuple[str, str], BulkSend]:
    """The sends of these (kind, about) pairs, by pair."""
    if not kind_abouts:
        return {}

    query = select(BulkSend).where(tuple_(BulkSend.kind, BulkSend.about).in_(kind_abouts))

    async with Session() as session:
        return {(send.kind, send.about): send for send in await session.scalars(query)}


async def unprepared() -> list[BulkSend]:
    """Sends whose recipients aren't all worked out yet: one being worked out a page at a time,
    one whose start couldn't, or a legal notice asked for before the bulk sender."""
    async with Session() as session:
        return list(
            await session.scalars(
                select(BulkSend).where(
                    BulkSend.prepared_at.is_(None), BulkSend.finished_at.is_(None)
                )
            )
        )


async def save_page(
    send_id: uuid.UUID, after: str, last: str, user_ids: list[str], done: bool
) -> bool:
    """Saves one page of the send's recipients, the audience read after `after`, and moves its
    cursor on to `last` (the page's last id); with `done`, the audience has ended and the send is
    prepared. The send's row is locked, and a page saved already (by a run at the same time: the
    cursor moved on) is left alone. False when it was."""
    async with Session() as session:
        send = await session.scalar(
            select(BulkSend)
            .where(BulkSend.id == send_id, BulkSend.prepared_at.is_(None))
            .with_for_update(skip_locked=True)
        )

        if send is None or (send.prepared_after or "") != after:
            return False

        for start in range(0, len(user_ids), INSERT_CHUNK):
            await session.execute(
                insert(BulkRecipient)
                .values(
                    [
                        {"send_id": send_id, "user_id": user_id}
                        for user_id in user_ids[start : start + INSERT_CHUNK]
                    ]
                )
                .on_conflict_do_nothing()
            )

        send.prepared_after = last

        if done:
            send.prepared_at = datetime.now(UTC)

        await session.commit()

    return True


async def finish_done() -> None:
    """Prepared sends with no pending recipient left are finished."""
    pending = exists().where(
        BulkRecipient.send_id == BulkSend.id, BulkRecipient.status == RecipientStatus.PENDING
    )

    async with Session() as session:
        await session.execute(
            update(BulkSend)
            .where(BulkSend.prepared_at.is_not(None), BulkSend.finished_at.is_(None), ~pending)
            .values(finished_at=datetime.now(UTC))
        )
        await session.commit()


async def stop(send_id: uuid.UUID) -> None:
    """Finishes the send at once: its pending recipients are skipped. A run sending one of them
    right now finishes that one first (its row is locked). Safe to repeat."""
    now = datetime.now(UTC)

    chosen = (
        select(BulkRecipient.id)
        .where(BulkRecipient.send_id == send_id, BulkRecipient.status == RecipientStatus.PENDING)
        .limit(DELETE_BATCH)
    )

    async with Session() as session:
        await session.execute(
            update(BulkSend)
            .where(BulkSend.id == send_id, BulkSend.finished_at.is_(None))
            .values(finished_at=now, stopped_at=now)
        )
        await session.commit()

    # Finished, the send gives no run another recipient; they're marked skipped a batch at a
    # time, as a send can go to every user.
    while True:
        async with Session() as session:
            skipped = await session.execute(
                update(BulkRecipient)
                .where(BulkRecipient.id.in_(chosen))
                .values(status=RecipientStatus.SKIPPED, reason=SkipReason.STOPPED)
            )
            await session.commit()

        if skipped.rowcount < DELETE_BATCH:
            return


def counted(condition):
    return func.count(case((condition, 1)))


async def counts(send_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    """Each send's recipients by status, and how many unsubscribed or complained after it."""
    query = (
        select(
            BulkRecipient.send_id,
            *(counted(BulkRecipient.status == status).label(status) for status in RecipientStatus),
            counted(BulkRecipient.unsubscribed_at.is_not(None)).label("unsubscribed"),
            counted(BulkRecipient.complained_at.is_not(None)).label("complained"),
        )
        .where(BulkRecipient.send_id.in_(send_ids))
        .group_by(BulkRecipient.send_id)
    )

    async with Session() as session:
        rows = (await session.execute(query)).mappings()

        return {row["send_id"]: {k: v for k, v in row.items() if k != "send_id"} for row in rows}
