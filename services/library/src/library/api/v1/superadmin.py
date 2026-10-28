from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.auth.user import Language, Level
from prepza_common.config.constants import MAX_TITLE_LENGTH
from prepza_common.db.paging import PageParams

from library.constants.sets import SetKind
from library.helpers.pools import missing
from library.schemas.feedback import ReportOut
from library.schemas.preparations import QuestionText, TitleIn
from library.schemas.templates import PooledTemplateOut, PoolTopicOut, TemplateSummary
from library.services import admin_quality, admin_templates, questions, templates

# The superadmin's templates (docs/features/admin-zone.md, Templates); everyone else gets "not found".
router = APIRouter(prefix="/superadmin/templates", tags=["superadmin"])


@router.get("")
async def list_templates(
    superadmin: SuperadminUser,
    page: PageParams,
    q: str = Query(default="", max_length=MAX_TITLE_LENGTH),
    level: Level | None = None,
    language: Annotated[list[Language] | None, Query()] = None,
) -> list[TemplateSummary]:
    return await templates.listed(q.strip(), level, language or [], page.offset, page.limit)


@router.get("/{template_id}")
async def get_template_detail(template_id: UUID, superadmin: SuperadminUser) -> PooledTemplateOut:
    """Its topics with their practice and company question counts, and whether a top-up has
    anything to write."""
    summary, topics = await admin_templates.with_pools(template_id)

    return PooledTemplateOut(
        **summary.model_dump(),
        topics=[
            PoolTopicOut(
                id=topic.id,
                title=topic.title,
                subtopics=topic.subtopics,
                practice_count=practice,
                company_count=company,
            )
            for topic, practice, company in topics
        ],
        short=any(any(missing(practice, company)) for _, practice, company in topics),
    )


@router.patch("/{template_id}/title", status_code=status.HTTP_204_NO_CONTENT)
async def rename_template(template_id: UUID, body: TitleIn, superadmin: SuperadminUser) -> None:
    await admin_templates.rename(template_id, body.title)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: UUID, superadmin: SuperadminUser) -> None:
    await admin_templates.delete(template_id)


@router.get("/{template_id}/topics/{topic_id}/questions")
async def list_topic_questions(
    template_id: UUID, topic_id: UUID, superadmin: SuperadminUser
) -> list[QuestionText]:
    """A topic's questions with their options and feedback counts."""
    found = await questions.topic_questions(topic_id)

    if found is None or found[0].id != template_id or found[0].kind != SetKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

    return found[1]


@router.get("/{template_id}/questions/{question_id}/reports")
async def list_question_reports(
    template_id: UUID, question_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ReportOut]:
    reports = await questions.reports(
        question_id, template_id, page.offset, page.limit, template=True
    )

    if reports is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    return [ReportOut.model_validate(report, from_attributes=True) for report in reports]


@router.post("/{template_id}/questions/{question_id}/wrong", status_code=status.HTTP_204_NO_CONTENT)
async def mark_wrong(template_id: UUID, question_id: UUID, superadmin: SuperadminUser) -> None:
    await admin_quality.mark_template_wrong(template_id, question_id)
