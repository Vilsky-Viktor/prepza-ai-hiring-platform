import uuid

from prepza_common.events.analytics import track
from prepza_common.limits.limits import question_seconds

from app.constants.events import GENERATION_CANCELLED, GENERATION_COMPLETED, GENERATION_FAILED
from app.helpers.notifications import interview_cancelled, interview_ready
from app.integrations.redis import get_redis
from app.services import outbox as outbox_service
from app.storage import interview_generations


async def handle(event_type: str, data: dict, event_id: str) -> None:
    """Stores what an interview generation produced, marks the interview of a failed one, or
    removes the interview of a cancelled one, and tells the company once, however often the
    event comes; other events aren't ours."""
    if event_type not in (GENERATION_COMPLETED, GENERATION_FAILED, GENERATION_CANCELLED):
        return

    generation_id = uuid.UUID(data["generation_id"])
    interview = await interview_generations.get_for_generation(generation_id)

    # Already removed: nothing to store, nobody to tell.
    if interview is None:
        return

    if event_type == GENERATION_COMPLETED:
        # An event from before generation sent the level keeps the seconds the test has.
        level = data.get("level")
        seconds = await question_seconds(get_redis(), level) if level else None
        await interview_generations.set_generated(
            generation_id,
            uuid.UUID(data["set_id"]),
            data["title"],
            seconds,
            interview_ready(interview, data["title"]),
            event_id,
        )
        await track("test_ready", company_id=interview.company_id, how="generated")
    elif event_type == GENERATION_FAILED:
        await interview_generations.mark_failed(generation_id, event_id)
    else:
        await interview_generations.remove_for_generation(
            generation_id, interview_cancelled(interview)
        )

    await outbox_service.flush_quietly()
