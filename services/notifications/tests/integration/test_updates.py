import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events.notifications import Recipient
from sqlalchemy import delete

from app.models.notifications import Notification
from app.storage import notifications, updates
from app.storage.db import Session
from tests.integration.factories import company

SINCE = datetime(2026, 10, 17, 9, tzinfo=UTC)
UNTIL = SINCE + timedelta(days=1)


async def stored(recipient: str, recipient_id: str, at: datetime) -> str:
    """A notification that came at `at`; its id."""
    row = Notification(
        event_id=str(uuid.uuid4()),
        recipient=recipient,
        recipient_id=recipient_id,
        kind="candidate_finished",
        link=f"/companies/{recipient_id}",
        data={"title": at.isoformat()},
        created_at=at,
    )

    async with Session() as session:
        session.add(row)
        await session.commit()

    return str(row.id)


async def forget(*recipient_ids: str) -> None:
    async with Session() as session:
        await session.execute(
            delete(Notification).where(Notification.recipient_id.in_(recipient_ids))
        )
        await session.commit()


def test_updates_are_the_companies_notifications_between_the_times_newest_first(run):
    first, second, other, user = company(), company(), company(), f"u-{uuid.uuid4()}"

    async def scenario():
        early = await stored(Recipient.COMPANY, first, SINCE + timedelta(hours=1))
        late = await stored(Recipient.COMPANY, second, SINCE + timedelta(hours=5))
        at_until = await stored(Recipient.COMPANY, first, UNTIL)
        await stored(Recipient.COMPANY, first, SINCE)
        await stored(Recipient.COMPANY, first, UNTIL + timedelta(seconds=1))
        await stored(Recipient.COMPANY, other, SINCE + timedelta(hours=2))
        await stored(Recipient.USER, first, SINCE + timedelta(hours=3))
        await stored(Recipient.USER, user, SINCE + timedelta(hours=3))

        try:
            rows = await updates.of_companies([first, second], SINCE, UNTIL)
        finally:
            await forget(first, second, other, user)

        return [(str(row.id), row.recipient_id) for row in rows], [
            (at_until, first),
            (late, second),
            (early, first),
        ]

    found, expected = run(scenario())

    assert found == expected


def test_reading_updates_marks_nothing_as_seen(run):
    shared, user = company(), f"u-{uuid.uuid4()}"
    recipients = [(Recipient.USER, user), (Recipient.COMPANY, shared)]

    async def scenario():
        await stored(Recipient.COMPANY, shared, SINCE + timedelta(hours=1))
        await stored(Recipient.COMPANY, shared, SINCE + timedelta(hours=2))

        try:
            before = await notifications.unread_count(recipients, user)
            read = await updates.of_companies([shared], SINCE, UNTIL)
            after = await notifications.unread_count(recipients, user)
        finally:
            await forget(shared)

        return before, len(read), after

    assert run(scenario()) == (2, 2, 2)
