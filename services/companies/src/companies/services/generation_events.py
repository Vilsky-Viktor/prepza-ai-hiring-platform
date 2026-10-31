"""An interview generation's outcome: what it produced is stored on its interview, a failed one
marks the interview, a cancelled one removes it; the company is told once, however often the
event comes. An interview already removed has nothing to store and nobody to tell."""

import uuid

from testee_common.events.analytics import track
from testee_common.limits.limits import question_seconds

from companies.core.db import Session
from companies.helpers.notifications import interview_cancelled, interview_ready
from companies.integrations.redis import get_redis
from companies.repositories import interview_generations
from companies.services import outbox as outbox_service


async def interview_of(generation_id: uuid.UUID):
    async with Session() as session:
        return await interview_generations.get_for_generation(session, generation_id)


async def completed(data: dict, event_id: str) -> None:
    generation_id = uuid.UUID(data["generation_id"])
    interview = await interview_of(generation_id)

    if interview is None:
        return

    # An event from before generation sent the level keeps the seconds the test has.
    level = data.get("level")
    seconds = await question_seconds(get_redis(), level) if level else None

    async with Session.begin() as session:
        await interview_generations.set_generated(
            session,
            generation_id,
            uuid.UUID(data["set_id"]),
            data["title"],
            seconds,
            interview_ready(interview, data["title"]),
            event_id,
        )

    await track("test_ready", company_id=interview.company_id, how="generated")
    await outbox_service.flush_quietly()


async def failed(data: dict, event_id: str) -> None:
    generation_id = uuid.UUID(data["generation_id"])

    if await interview_of(generation_id) is None:
        return

    async with Session.begin() as session:
        await interview_generations.mark_failed(session, generation_id, event_id)

    await outbox_service.flush_quietly()


async def cancelled(data: dict, event_id: str) -> None:
    generation_id = uuid.UUID(data["generation_id"])
    interview = await interview_of(generation_id)

    if interview is None:
        return

    async with Session.begin() as session:
        await interview_generations.remove_for_generation(
            session, generation_id, interview_cancelled(interview)
        )

    await outbox_service.flush_quietly()
