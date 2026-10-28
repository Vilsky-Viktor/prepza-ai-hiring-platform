import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events import outbox, pubsub
from sqlalchemy import select

from generation.constants.statuses import Status
from generation.core.db import Session
from generation.models.outbox import OutboxEvent
from generation.repositories import generations
from generation.services import outbox as outbox_service
from generation.services import schedules
from tests.integration.transactions import transaction


async def waiting():
    async with Session() as session:
        return list(
            await session.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None)))
        )


def test_an_expired_interview_review_saves_its_event_and_the_flush_publishes_it(run, published):
    async def scenario():
        interview = await transaction(generations.create, "ann", "job", uuid.uuid4())
        await transaction(generations.update, interview.id, status=Status.AWAITING_REVIEW)

        await schedules.cancel_reviews(datetime.now(UTC) + timedelta(seconds=1))
        saved = [(row.event_type, row.data) for row in await waiting()]
        flushed = await outbox_service.flush()

        return interview.id, saved, flushed, await waiting()

    interview_id, saved, flushed, left = run(scenario())

    expected = ("generation.cancelled", {"generation_id": str(interview_id)})
    assert expected in saved
    assert expected in published
    assert flushed == len(saved)
    assert left == []


def test_a_failed_publish_leaves_the_event_for_the_next_flush(run, monkeypatch):
    async def down(messages, timeout):
        raise ConnectionError("Pub/Sub is down")

    monkeypatch.setattr(pubsub, "publish_batch", down)

    async def scenario():
        async with Session() as session:
            outbox.add(session, OutboxEvent, "test.event", {"n": 1})
            await session.commit()

        await outbox_service.flush_quietly()

        return [row.event_type for row in await waiting()]

    assert "test.event" in run(scenario())


def test_a_stuck_interview_generation_saves_its_failed_event_and_a_template_none(run):
    async def scenario():
        interview = await transaction(generations.create, "ann", "job", uuid.uuid4())
        template = await transaction(generations.create, "ann", "template", kind="template")
        await transaction(generations.claim_run, interview.id)
        await transaction(generations.claim_run, template.id)
        later = datetime.now(UTC) + timedelta(seconds=1)
        await schedules.fail_stuck(later, later)
        saved = [(row.event_type, row.data) for row in await waiting()]

        return interview.id, template.id, saved

    interview_id, template_id, saved = run(scenario())

    assert ("generation.failed", {"generation_id": str(interview_id)}) in saved
    assert ("generation.failed", {"generation_id": str(template_id)}) not in saved
