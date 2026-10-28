from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams
from prepza_common.limits.pause import refuse_if_paused

from companies.api.dependencies import Via
from companies.constants.invites import MAX_SEARCH_LENGTH
from companies.integrations.redis import get_redis
from companies.schemas.interviews import (
    InterviewCreate,
    InterviewDetail,
    InterviewFromTemplate,
    InterviewOut,
    InterviewSettings,
    PreviewOut,
    TitleIn,
)
from companies.schemas.invites import StartIn
from companies.services import (
    interview_changes,
    interview_creation,
    interview_removal,
    interview_views,
    previews,
)
from companies.services.access import refuse_without_pledge, require_company, require_editor
from companies.services.interview_access import interview_for

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_interview(
    body: InterviewCreate, company_id: UUID, user: CurrentUser
) -> InterviewOut:
    await refuse_if_paused(get_redis(), "interview_generation", company_id, user.uid)
    company, _ = await require_editor(user, company_id)

    return await interview_creation.create(
        company, user.uid, user.language, body.text, body.generate_in
    )


@router.post("/from-template", status_code=status.HTTP_201_CREATED)
async def create_from_template(
    body: InterviewFromTemplate, company_id: UUID, user: CurrentUser
) -> InterviewOut:
    """A test copied from a template: free and ready at once, so no generation limits apply."""
    company, _ = await require_editor(user, company_id)

    return await interview_creation.create_from_template(company, user.uid, body.template_id)


@router.get("")
async def list_interviews(
    company_id: UUID,
    user: CurrentUser,
    page: PageParams,
    q: Annotated[str, Query(max_length=MAX_SEARCH_LENGTH)] = "",
) -> list[InterviewOut]:
    """The company's interviews, newest first; `q` narrows them to titles containing it."""
    company, _ = await require_company(user, company_id)

    return await interview_views.interviews_page(company.id, page.offset, page.limit, q.strip())


@router.get("/{interview_id}")
async def get_interview(interview_id: UUID, user: CurrentUser) -> InterviewDetail:
    interview, _, member = await interview_for(user, interview_id)

    return await interview_views.detail(interview, member)


@router.patch("/{interview_id}/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_settings(
    interview_id: UUID, body: InterviewSettings, user: CurrentUser, via: Via
) -> None:
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    await interview_changes.update_settings(interview, body, user.uid, via)


@router.patch("/{interview_id}/title", status_code=status.HTTP_204_NO_CONTENT)
async def rename_interview(interview_id: UUID, body: TitleIn, user: CurrentUser) -> None:
    """Company owners and admins can rename an interview once it has been generated."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    await interview_changes.rename(interview, body.title, user.uid)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(interview_id: UUID, user: CurrentUser) -> None:
    """Credits, results and questions go first, so a failure leaves the interview to delete
    again."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    await interview_removal.delete(interview, user.uid)


@router.post("/{interview_id}/preview", status_code=status.HTTP_201_CREATED)
async def preview_interview(
    interview_id: UUID, user: CurrentUser, body: StartIn | None = None
) -> PreviewOut:
    """A company member takes their own test as a candidate would: free, kept out of the
    candidate list, and its answers out of the questions' statistics. Each preview is new, and
    starts with the pledge a candidate gives."""
    await refuse_if_paused(get_redis(), "preview", user_id=user.uid)
    interview, _, _ = await interview_for(user, interview_id)
    refuse_without_pledge(body is not None and body.pledged, None)

    return PreviewOut(session_id=await previews.preview(interview, user.uid))
