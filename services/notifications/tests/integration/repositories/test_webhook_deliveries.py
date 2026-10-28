"""A Resend web hook is recorded once per delivery, as the event its work runs from."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from notifications.constants.events import EMAIL_WEBHOOK
from notifications.core.db import Session
from notifications.models.outbox import OutboxEvent
from notifications.repositories import webhook_deliveries
from tests.integration.transactions import transaction


def test_a_delivery_is_recorded_once_however_often_it_comes(run):
    delivery = f"msg_{uuid.uuid4().hex}"
    event = {"type": "email.bounced", "data": {"tags": {"kind": "digest"}}}

    async def scenario():
        await transaction(webhook_deliveries.record, delivery, event)

        # Resend sending it again: its delivery's event is there already.
        with pytest.raises(IntegrityError):
            await transaction(webhook_deliveries.record, delivery, event)

        async with Session() as session:
            rows = list(
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.id == uuid.uuid5(uuid.NAMESPACE_URL, f"resend:{delivery}")
                    )
                )
            )

        return [(row.event_type, row.data) for row in rows]

    assert run(scenario()) == [(EMAIL_WEBHOOK, {"event": event})]
