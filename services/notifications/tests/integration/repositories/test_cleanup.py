import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select

from notifications.constants.notifications import EXPIRED_PER_PRUNE, KEEP_DAYS, MAX_PER_RECIPIENT
from notifications.core.db import Session
from notifications.models.notifications import Notification, Received
from notifications.repositories import notifications
from tests.integration.factories import company, finished


def expired_at() -> datetime:
    return datetime.now(UTC) - timedelta(days=KEEP_DAYS + 1)


def row(company_id: str, created_at: datetime) -> Notification:
    return Notification(
        event_id=str(uuid.uuid4()),
        recipient="company",
        recipient_id=company_id,
        kind="interview_ready",
        link="/x",
        data={},
        created_at=created_at,
    )


async def store_expired(count: int) -> None:
    """Starts from no expired rows (the database is shared by the run), then adds `count` of
    each table."""
    async with Session() as session:
        await session.execute(delete(Notification).where(Notification.created_at < expired_at()))
        await session.execute(delete(Received).where(Received.received_at < expired_at()))
        session.add_all(row(company(), expired_at()) for _ in range(count))
        session.add_all(
            Received(event_id=str(uuid.uuid4()), received_at=expired_at()) for _ in range(count)
        )
        await session.commit()


async def count_expired() -> tuple[int, int]:
    async with Session() as session:
        rows = await session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.created_at < expired_at())
        )
        events = await session.scalar(
            select(func.count()).select_from(Received).where(Received.received_at < expired_at())
        )

        return rows, events


def test_each_new_notification_removes_a_bounded_batch_of_expired_rows(run):
    async def scenario():
        await store_expired(EXPIRED_PER_PRUNE + 5)
        await notifications.add(str(uuid.uuid4()), finished(company()))
        after_one = await count_expired()
        await notifications.add(str(uuid.uuid4()), finished(company()))

        return after_one, await count_expired()

    assert run(scenario()) == ((5, 5), (0, 0))


def test_cleanup_skips_expired_rows_another_call_holds_and_never_waits(run):
    async def scenario():
        await store_expired(3)

        async with Session() as holder:
            # Another call is removing these right now.
            held = list(
                await holder.scalars(
                    select(Notification.id)
                    .where(Notification.created_at < expired_at())
                    .with_for_update()
                )
            )
            held_events = list(
                await holder.scalars(
                    select(Received.event_id)
                    .where(Received.received_at < expired_at())
                    .with_for_update()
                )
            )
            added = await asyncio.wait_for(
                notifications.add(str(uuid.uuid4()), finished(company())), 5
            )
            await holder.rollback()

        return len(held), len(held_events), added, await count_expired()

    # The new notification was stored without waiting; the held rows are left for later.
    assert run(scenario()) == (3, 3, True, (3, 3))


def test_a_recipient_keeps_only_their_newest(run):
    company_id = company()

    async def scenario():
        now = datetime.now(UTC)

        async with Session() as session:
            session.add_all(
                row(company_id, now - timedelta(minutes=MAX_PER_RECIPIENT - number))
                for number in range(MAX_PER_RECIPIENT)
            )
            await session.commit()

        await notifications.add(str(uuid.uuid4()), finished(company_id))
        kept = await notifications.latest([("company", company_id)], limit=None)

        return len(kept), kept[0].kind, min(item.created_at for item in kept)

    kept, newest, oldest = run(scenario())

    assert (kept, newest) == (MAX_PER_RECIPIENT, "candidate_finished")
    # The oldest went; the one just after it stayed.
    assert oldest > datetime.now(UTC) - timedelta(minutes=MAX_PER_RECIPIENT)
