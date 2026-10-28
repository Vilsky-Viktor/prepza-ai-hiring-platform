import base64
import json
import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events import outbox, pubsub
from sqlalchemy import select

from generation.constants.statuses import Status
from generation.core.db import Session
from generation.models.outbox import OutboxEvent
from generation.repositories import generations
from generation.services import outbox as outbox_service


async def waiting():
    async with Session() as session:
        return list(
            await session.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None)))
        )


def test_an_expired_interview_review_saves_its_event_and_the_flush_publishes_it(run, monkeypatch):
    sent = []

    async def publish_batch(messages, timeout):
        sent.extend(
            (message["attributes"]["type"], json.loads(base64.b64decode(message["data"])))
            for message in messages
        )

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    async def scenario():
        interview = await generations.create("ann", "job", uuid.uuid4())
        await generations.update(interview.id, status=Status.AWAITING_REVIEW)

        await generations.expire_reviews(datetime.now(UTC) + timedelta(seconds=1))
        saved = [(row.event_type, row.data) for row in await waiting()]
        published = await outbox_service.flush()

        return interview.id, saved, published, await waiting()

    interview_id, saved, published, left = run(scenario())

    expected = ("generation.cancelled", {"generation_id": str(interview_id)})
    assert expected in saved
    assert expected in sent
    assert published == len(saved)
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
        interview = await generations.create("ann", "job", uuid.uuid4())
        template = await generations.create("ann", "template", kind="template")
        await generations.claim_run(interview.id)
        await generations.claim_run(template.id)
        later = datetime.now(UTC) + timedelta(seconds=1)
        await generations.fail_stuck(later, later, "stopped")
        saved = [(row.event_type, row.data) for row in await waiting()]

        return interview.id, template.id, saved

    interview_id, template_id, saved = run(scenario())

    assert ("generation.failed", {"generation_id": str(interview_id)}) in saved
    assert ("generation.failed", {"generation_id": str(template_id)}) not in saved
