import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events.notifications import (
    NOTIFICATION_REQUESTED,
    NotificationKind,
    notification,
)
from sqlalchemy import func, select, update

from app.constants.notifications import GROUP_HOURS
from app.models.notifications import Notification, Received
from app.storage import notifications
from app.storage.db import Session
from tests.integration.factories import api, company, finished, push


async def rows(company_id: str) -> list[Notification]:
    async with Session() as session:
        found = await session.scalars(
            select(Notification)
            .where(Notification.recipient_id == company_id)
            .order_by(Notification.created_at)
        )

        return list(found)


def test_a_redelivered_event_makes_one_notification(run):
    company_id = company()
    event = notification("company", company_id, NotificationKind.INTERVIEW_READY, "/x", title="T")

    async def scenario():
        async with api() as client:
            # Pub/Sub's own retry (same message id), then the outbox re-sending it (a new
            # message id, the same outbox id).
            answers = [
                await client.post("/internal/events", json=push(*args))
                for args in [
                    (NOTIFICATION_REQUESTED, event, "outbox-1", "m-1"),
                    (NOTIFICATION_REQUESTED, event, "outbox-1", "m-1"),
                    (NOTIFICATION_REQUESTED, event, "outbox-1", "m-2"),
                ]
            ]

        async with Session() as session:
            received = await session.scalar(
                select(func.count()).select_from(Received).where(Received.event_id == "outbox-1")
            )

        return [answer.status_code for answer in answers], received, await rows(company_id)

    codes, received, saved = run(scenario())

    assert codes == [204, 204, 204]
    assert received == 1
    assert [row.event_id for row in saved] == ["outbox-1"]


def test_the_same_key_from_different_events_makes_one_notification(run):
    company_id = company()
    event = notification(
        "company", company_id, NotificationKind.INTERVIEW_READY, "/x", key="invite-1", title="T"
    )

    async def scenario():
        async with api() as client:
            answers = [
                await client.post(
                    "/internal/events",
                    json=push(NOTIFICATION_REQUESTED, event, str(uuid.uuid4()), message_id),
                )
                for message_id in ["m-k1", "m-k2"]
            ]

        return [answer.status_code for answer in answers], await rows(company_id)

    codes, saved = run(scenario())

    assert codes == [204, 204]
    assert [row.event_id for row in saved] == ["interview_ready:invite-1"]


def test_candidates_finishing_one_test_add_up_in_one_notification(run):
    company_id = company()

    async def scenario():
        for email in ["a@x.com", "b@x.com", "c@x.com"]:
            await notifications.add(str(uuid.uuid4()), finished(company_id, email=email))

        # A retried event of the group doesn't count twice.
        await notifications.add("retried", finished(company_id, email="d@x.com"))
        await notifications.add("retried", finished(company_id, email="d@x.com"))

        return await rows(company_id)

    [group] = run(scenario())

    assert group.data == {"title": "Backend", "email": "d@x.com", "count": 4}


def test_another_test_or_an_ungrouped_kind_makes_its_own_notification(run):
    company_id = company()
    ready = notification("company", company_id, NotificationKind.INTERVIEW_READY, "/x", title="T")

    async def scenario():
        await notifications.add(str(uuid.uuid4()), finished(company_id, "Backend"))
        await notifications.add(str(uuid.uuid4()), finished(company_id, "Frontend"))
        await notifications.add(str(uuid.uuid4()), ready)
        await notifications.add(str(uuid.uuid4()), ready)

        return await rows(company_id)

    saved = run(scenario())

    assert sorted((row.kind, row.data.get("title"), row.data.get("count")) for row in saved) == [
        ("candidate_finished", "Backend", None),
        ("candidate_finished", "Frontend", None),
        ("interview_ready", "T", None),
        ("interview_ready", "T", None),
    ]


def test_a_group_older_than_the_window_starts_a_new_one(run):
    company_id = company()

    async def scenario():
        await notifications.add(str(uuid.uuid4()), finished(company_id))

        async with Session() as session:
            await session.execute(
                update(Notification)
                .where(Notification.recipient_id == company_id)
                .values(created_at=datetime.now(UTC) - timedelta(hours=GROUP_HOURS + 1))
            )
            await session.commit()

        await notifications.add(str(uuid.uuid4()), finished(company_id))
        await notifications.add(str(uuid.uuid4()), finished(company_id))

        return await rows(company_id)

    old, new = run(scenario())

    assert "count" not in old.data
    assert new.data["count"] == 2
