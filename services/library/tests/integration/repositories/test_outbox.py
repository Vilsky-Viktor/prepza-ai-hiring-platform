import uuid

from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import select

from library.core.db import Session
from library.models.outbox import OutboxEvent
from library.repositories import quality
from tests.integration.factories import a_company, interview, question_ids
from tests.integration.transactions import transaction


def test_a_flag_and_its_notification_are_saved_together(run):
    notice = {"recipient": "company", "recipient_id": a_company("1"), "marker": str(uuid.uuid4())}

    async def scenario():
        [question_id, *_] = await question_ids(await interview())
        await transaction(quality.save_flag, question_id, "wrong_key", notice=notice)

        async with Session() as session:
            events = list(
                await session.scalars(
                    select(OutboxEvent).where(OutboxEvent.event_type == NOTIFICATION_REQUESTED)
                )
            )

        return [event.data for event in events]

    assert notice in run(scenario())
