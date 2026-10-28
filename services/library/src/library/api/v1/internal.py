from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.ai.examples import has_example
from prepza_common.ai.multi_answer import is_multi, multi_share
from prepza_common.ai.sets import PreparationIn
from prepza_common.db.paging import PageParams

from library.api.dependencies import ServiceCaller
from library.integrations.redis import get_redis
from library.repositories import feedback, preparations, templates
from library.schemas.feedback import ReportOut
from library.schemas.preparations import (
    CreatedOut,
    QuestionOut,
    QuestionText,
    TitleIn,
    TopicOut,
)
from library.schemas.regenerate import QuestionContext, QuestionReplace
from library.schemas.sets import SetContent, SetOut, SetTopicOut
from library.schemas.templates import TemplateCopyIn, TemplateCopyOut
from library.services import outbox as outbox_service
from library.services.questions import question_texts
from library.services.set_saves import save_once

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/interviews", status_code=status.HTTP_201_CREATED)
async def create_interview(body: PreparationIn, caller: ServiceCaller) -> CreatedOut:
    """A retried save from the same generation returns the set it already made."""

    async def create() -> UUID:
        return await preparations.create_interview(body)

    return CreatedOut(id=await save_once(body.generation_id, create))


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(body: PreparationIn, caller: ServiceCaller) -> CreatedOut:
    """A retried save from the same generation returns the template it already made."""

    async def create() -> UUID:
        return await templates.create_template(body, await multi_share(get_redis()))

    return CreatedOut(id=await save_once(body.generation_id, create))


@router.post("/templates/{template_id}/copy", status_code=status.HTTP_201_CREATED)
async def copy_template(
    template_id: UUID, body: TemplateCopyIn, caller: ServiceCaller
) -> TemplateCopyOut:
    """For companies: a company's own test made from a template, with no generation."""
    copy = await templates.copy_template(template_id, body.company_id)

    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    return TemplateCopyOut(id=copy.id, title=copy.title, language=copy.language, level=copy.level)


@router.delete("/interviews/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(set_id: UUID, caller: ServiceCaller) -> None:
    """Deletes an interview set; safe to repeat."""
    if await preparations.get(set_id) is not None:
        await preparations.remove(set_id)


@router.patch("/sets/{set_id}/title", status_code=status.HTTP_204_NO_CONTENT)
async def rename_set(set_id: UUID, body: TitleIn, caller: ServiceCaller) -> None:
    if await preparations.get(set_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Set not found")

    await preparations.set_title(set_id, body.title)


@router.get("/sets/{set_id}")
async def get_set(set_id: UUID, caller: ServiceCaller) -> SetOut:
    question_set = await preparations.get(set_id)

    if question_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Set not found")

    topics = await preparations.get_topics(set_id)

    return SetOut(
        id=question_set.id,
        kind=question_set.kind,
        owner_id=question_set.owner_id,
        title=question_set.title,
        level=question_set.level,
        language=question_set.language,
        topics=[
            TopicOut(
                id=topic.id,
                title=topic.title,
                subtopics=topic.subtopics,
                question_count=question_count,
            )
            for topic, question_count in topics
        ],
    )


@router.get("/sets/{set_id}/content")
async def get_set_content(set_id: UUID, caller: ServiceCaller) -> SetContent:
    question_set = await preparations.get_content(set_id)

    if question_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Set not found")

    return SetContent(
        id=question_set.id,
        title=question_set.title,
        level=question_set.level,
        topics=[
            SetTopicOut(
                id=topic.id,
                title=topic.title,
                questions=[
                    QuestionOut(
                        id=question.id,
                        text=question.text,
                        options=question.options,
                    )
                    for question in topic.questions
                ],
            )
            for topic in question_set.topics
            # Every question of a topic can be left out (storage served()).
            if topic.questions
        ],
    )


@router.get("/sets/{set_id}/topics/{topic_id}/questions")
async def list_topic_questions(
    set_id: UUID, topic_id: UUID, caller: ServiceCaller
) -> list[QuestionText]:
    """One topic's questions in a set, with their options and feedback counts."""
    found = await preparations.get_topic_with_question_texts(topic_id)

    if found is None or found[0].id != set_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

    return await question_texts(found[1].questions)


@router.get("/sets/{set_id}/questions/{question_id}/reports")
async def list_question_reports(
    set_id: UUID, question_id: UUID, caller: ServiceCaller, page: PageParams
) -> list[ReportOut]:
    question_set = await preparations.get_for_question(question_id)

    if question_set is None or question_set.id != set_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    reports = await feedback.list_reports(question_id, page.offset, page.limit)

    return [ReportOut.model_validate(report, from_attributes=True) for report in reports]


@router.get("/questions/{question_id}/context")
async def get_question_context(question_id: UUID, caller: ServiceCaller) -> QuestionContext:
    found = await preparations.get_question_context(question_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    question_set, topic = found
    question = next(item for item in topic.questions if item.id == question_id)

    return QuestionContext(
        set_id=question_set.id,
        kind=question_set.kind,
        owner_id=question_set.owner_id,
        level=question_set.level,
        language=question_set.language,
        topic=topic.title,
        subtopics=topic.subtopics,
        existing=[item.text for item in topic.questions],
        multi=is_multi(question.options),
        example=has_example(question.text),
    )


@router.put("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def replace_question(question_id: UUID, body: QuestionReplace, caller: ServiceCaller) -> None:
    """New content in the question's slot, for candidates who start after it; those who already
    answered keep their own copy of the question, and their marks."""
    options = [option.model_dump() for option in body.options]
    await preparations.replace_question(question_id, body.text, options)
    await outbox_service.flush_quietly()
