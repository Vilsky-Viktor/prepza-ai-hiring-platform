from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from library.api.dependencies import ServiceCaller
from library.constants.sets import Pool, SetKind
from library.core.db import Session
from library.repositories import practice_matches, preparations
from library.schemas.sets import ContentQuestion, PracticeTopicsOut, SetContent, SetTopicOut

# Free practice for talents: only a template's practice questions, never its company ones.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/templates/{template_id}/practice")
async def practice_content(template_id: UUID, caller: ServiceCaller) -> SetContent:
    """The template's practice questions, with answers, by topic; topics without any are left
    out. Rounds picks each practice round's questions from them."""
    async with Session() as session:
        template = await preparations.get_content(session, template_id)

    if template is None or template.kind != SetKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    topics = [
        SetTopicOut(
            id=topic.id,
            title=topic.title,
            questions=[
                ContentQuestion(id=question.id, text=question.text, options=question.options)
                for question in topic.questions
                if question.pool == Pool.PRACTICE
            ],
        )
        for topic in template.topics
    ]

    return SetContent(
        id=template.id,
        title=template.title,
        level=template.level,
        topics=[topic for topic in topics if topic.questions],
    )


@router.get("/sets/{set_id}/practice-topics")
async def practice_topics(set_id: UUID, caller: ServiceCaller) -> PracticeTopicsOut:
    """Companies, for an interview's Discover tab: the template topics of the interview's level
    on the same subjects as its topics, whose practice results count there."""
    async with Session() as session:
        found = await practice_matches.practice_topics(session, set_id)

    return PracticeTopicsOut(topic_ids=found)
