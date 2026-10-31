from uuid import UUID

from fastapi import APIRouter, status
from testee_common.ai.sets import AddedQuestionsIn, AdditionContext, AdditionTopic

from library.api.dependencies import ServiceCaller
from library.constants.sets import Pool
from library.helpers.pools import missing
from library.services import additions

# For generation: adding questions to a template's topics, a top-up or a superadmin's addition
# (docs/features/admin-zone.md, Templates).
router = APIRouter(prefix="/internal/templates", tags=["internal"])


@router.get("/{template_id}/additions")
async def addition_context(template_id: UUID, caller: ServiceCaller) -> AdditionContext:
    """Each topic with every question's text, and what it lacks of each pool."""
    template, found = await additions.context(template_id)
    topics = []

    for topic in found:
        practice_missing, company_missing = missing(
            sum(question.pool == Pool.PRACTICE for question in topic.questions),
            sum(question.pool == Pool.COMPANY for question in topic.questions),
        )
        topics.append(
            AdditionTopic(
                id=topic.id,
                title=topic.title,
                subtopics=topic.subtopics,
                texts=[question.text for question in topic.questions],
                practice_missing=practice_missing,
                company_missing=company_missing,
            )
        )

    return AdditionContext(level=template.level, language=template.language, topics=topics)


@router.post("/{template_id}/questions", status_code=status.HTTP_201_CREATED)
async def add_questions(
    template_id: UUID, body: AddedQuestionsIn, caller: ServiceCaller
) -> list[list[UUID]]:
    """Saves the new questions of every topic at once; each topic's new question ids, for the
    answer-key checks. Interviews already copied from the template don't change."""
    return await additions.add(template_id, body.topics)
