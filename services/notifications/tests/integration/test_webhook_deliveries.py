"""A Resend web hook is recorded once per delivery, as the event its work runs from."""

import uuid

from sqlalchemy import select

from app.constants.events import EMAIL_WEBHOOK
from app.models.outbox import OutboxEvent
from app.storage import webhook_deliveries
from app.storage.db import Session


def test_a_delivery_is_recorded_once_however_often_it_comes(run):
    delivery = f"msg_{uuid.uuid4().hex}"
    event = {"type": "email.bounced", "data": {"tags": {"kind": "digest"}}}

    async def scenario():
        first = await webhook_deliveries.record(delivery, event)
        again = await webhook_deliveries.record(delivery, event)

        async with Session() as session:
            rows = list(
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.id == uuid.uuid5(uuid.NAMESPACE_URL, f"resend:{delivery}")
                    )
                )
            )

        return first, again, [(row.event_type, row.data) for row in rows]

    first, again, rows = run(scenario())

    assert (first, again) == (True, False)
    assert rows == [(EMAIL_WEBHOOK, {"event": event})]
