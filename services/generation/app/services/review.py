from fastapi import HTTPException, status
from prepza_common.i18n.i18n import TemplateError
from prepza_common.limits.rate_limit import hit

from app.constants.generation import (
    NOT_AWAITING_REVIEW,
    RUN_GENERATION,
    TOO_MANY_CHOSEN,
    TOO_MANY_REVISIONS,
    TOO_MANY_SUBTOPICS,
)
from app.constants.statuses import Status
from app.integrations import tasks
from app.integrations.redis import get_redis
from app.models.generation import Generation
from app.schemas.generation import ReviewRequest
from app.services.topic_caps import topic_caps
from app.storage import generations


async def submit_review(generation: Generation, body: ReviewRequest) -> Generation:
    """Queues the reviewed topics; only one review wins for a generation awaiting review. The
    selection must name drafted topics, and a generation's topics are revised in words (a model
    call each) at most MAX_TOPIC_REVISIONS times."""
    drafted = len(generation.topics or [])

    if any(not 0 <= index < drafted for index in body.selected):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choose topics from the list")

    caps = await topic_caps()

    # Without instructions the review approves the selection, which caps the topics. With
    # instructions the topics are revised first, so the reviewer may ask to merge.
    if not body.instructions.strip() and len(body.selected) > caps["max_topics"]:
        raise TemplateError(
            status.HTTP_422_UNPROCESSABLE_CONTENT, TOO_MANY_CHOSEN, count=caps["max_topics"]
        )

    if any(len(topic.subtopics) > caps["max_subtopics"] for topic in body.topics or []):
        raise TemplateError(
            status.HTTP_422_UNPROCESSABLE_CONTENT, TOO_MANY_SUBTOPICS, count=caps["max_subtopics"]
        )

    # Refused before it counts a revision; the claim below still settles two reviews at once.
    if generation.status != Status.AWAITING_REVIEW:
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_AWAITING_REVIEW)

    if body.instructions.strip():
        await hit(
            get_redis(),
            f"rate:revisions:{generation.id}",
            "MAX_TOPIC_REVISIONS",
            TOO_MANY_REVISIONS,
            company_id=generation.company_id,
            user_id=generation.owner_uid,
        )

    if not await generations.claim_review(generation.id):
        raise HTTPException(status.HTTP_409_CONFLICT, NOT_AWAITING_REVIEW)

    await tasks.enqueue(
        RUN_GENERATION, {"generation_id": str(generation.id), "resume": body.model_dump()}
    )

    return await generations.get(generation.id)
