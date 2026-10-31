from typing import Annotated

from fastapi import APIRouter, Query
from testee_common.auth.user import Language, Level
from testee_common.config.constants import LANGUAGES, LEVELS, MAX_TITLE_LENGTH
from testee_common.db.paging import PageParams

from library.constants.templates import SAMPLE_QUESTIONS
from library.schemas.preparations import TopicOut
from library.schemas.templates import (
    SampleQuestionOut,
    TemplateFiltersOut,
    TemplateOut,
    TemplateSummary,
)
from library.services import templates

# Templates: public, for the practice pages search engines index and for companies to start a
# test from. Topics, and a sample of the practice questions practice shows anyway; never the
# company ones. Only superadmins change them.
router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/filters")
async def template_filters() -> TemplateFiltersOut:
    return TemplateFiltersOut(levels=list(LEVELS), languages=list(LANGUAGES))


@router.get("")
async def list_templates(
    page: PageParams,
    q: str = Query(default="", max_length=MAX_TITLE_LENGTH),
    level: Level | None = None,
    language: Annotated[list[Language] | None, Query()] = None,
) -> list[TemplateSummary]:
    return await templates.listed(q.strip(), level, language or [], page.offset, page.limit)


@router.get("/copyable")
async def list_copyable_templates(
    page: PageParams,
    q: str = Query(default="", max_length=MAX_TITLE_LENGTH),
    level: Level | None = None,
    language: Annotated[list[Language] | None, Query()] = None,
) -> list[TemplateSummary]:
    """The templates a company can start a test from: only those it can copy, so using one never
    fails. Practice lists every template."""
    return await templates.listed(
        q.strip(), level, language or [], page.offset, page.limit, copyable=True
    )


@router.get("/{key}")
async def get_template(key: str) -> TemplateOut:
    """A template's topics and subtopics, by its id or slug, to review before using it."""
    summary, topics = await templates.with_topics(key)

    return TemplateOut(
        **summary.model_dump(),
        topics=[
            TopicOut(
                id=topic.id, title=topic.title, subtopics=topic.subtopics, question_count=count
            )
            for topic, count in topics
        ],
    )


@router.get("/{key}/sample")
async def sample_questions(key: str) -> list[SampleQuestionOut]:
    """A few of the template's practice questions, with answers, spread across its topics, for
    its practice page. Company questions are never shown."""
    rows = await templates.sample(key, SAMPLE_QUESTIONS)

    return [
        SampleQuestionOut(id=question.id, topic=topic, text=question.text, options=question.options)
        for question, topic in rows
    ]
