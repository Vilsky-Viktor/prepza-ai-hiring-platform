from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.analytics import track
from prepza_common.audit_actions import AuditAction
from prepza_common.auth import CurrentUser
from prepza_common.limits import question_seconds
from prepza_common.multi_answer import multi_share
from prepza_common.paging import PageParams
from prepza_common.pause import refuse_if_paused
from prepza_common.rate_limit import hit

from app.constants.invites import INTERVIEW_NOT_READY, MAX_SEARCH_LENGTH
from app.helpers.interviews import (
    attach_set,
    attach_set_if_reachable,
    interview_minutes,
    interview_out,
    interview_questions,
    interviews_page,
    session_topics,
    topics_out,
)
from app.integrations import library, rounds
from app.integrations.redis import get_redis
from app.schemas.interviews import (
    InterviewCreate,
    InterviewDetail,
    InterviewFromTemplate,
    InterviewOut,
    InterviewSettings,
    PreviewOut,
    TitleIn,
)
from app.service_auth import Via
from app.services import interview_creation, set_cache
from app.services.access import can_edit, require_company, require_editor
from app.services.candidate_billing import release_unfinished, settle_removed
from app.services.interview_access import interview_for
from app.storage import audit, candidates, interviews, invites

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
    copy = await library.copy_template(body.template_id, company.id)

    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    seconds = await question_seconds(get_redis(), copy["level"])
    interview = await interviews.create_from_template(
        company.id, copy["id"], copy["title"], copy["language"], seconds
    )
    await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_FROM_TEMPLATE)
    await track(
        "interview_from_template", user_id=user.uid, company_id=company.id, set_id=copy["id"]
    )
    # Ready at once: no generation to wait for.
    await track("test_ready", user_id=user.uid, company_id=company.id, how="template")

    return await interview_out(interview)


@router.get("")
async def list_interviews(
    company_id: UUID,
    user: CurrentUser,
    page: PageParams,
    q: Annotated[str, Query(max_length=MAX_SEARCH_LENGTH)] = "",
) -> list[InterviewOut]:
    """The company's interviews, newest first; `q` narrows them to titles containing it."""
    company, _ = await require_company(user, company_id)

    return await interviews_page(company.id, page.offset, page.limit, q.strip())


@router.get("/{interview_id}")
async def get_interview(interview_id: UUID, user: CurrentUser) -> InterviewDetail:
    interview, _, member = await interview_for(user, interview_id)
    interview = await attach_set_if_reachable(interview)
    totals = await candidates.counts([interview.id])
    base = await interview_out(interview, totals.get(interview.id, 0))
    found = await set_cache.get_set(interview.set_id) if interview.set_id else None

    topics = topics_out(found, interview.topic_limits) if found else []

    return InterviewDetail(
        **base.model_dump(),
        company_id=interview.company_id,
        topics=topics,
        total_minutes=interview_minutes(found, interview.topic_limits, interview.question_seconds),
        total_questions=interview_questions(found, interview.topic_limits),
        can_edit=can_edit(member),
    )


@router.patch("/{interview_id}/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_settings(
    interview_id: UUID, body: InterviewSettings, user: CurrentUser, via: Via
) -> None:
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    await interviews.update_settings(interview.id, body)
    changed = (
        body.question_seconds is not None and body.question_seconds != interview.question_seconds
    ) or (body.hired is not None and body.hired != interview.hired)

    if changed:
        await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_SETTINGS_CHANGED)

    if body.pass_mark is not None and body.pass_mark != interview.pass_mark:
        await audit.record_interview(interview, user.uid, AuditAction.PASS_MARK_CHANGED, via)


@router.patch("/{interview_id}/title", status_code=status.HTTP_204_NO_CONTENT)
async def rename_interview(interview_id: UUID, body: TitleIn, user: CurrentUser) -> None:
    """Company owners and admins can rename an interview once it has been generated."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, INTERVIEW_NOT_READY)

    await library.rename_set(interview.set_id, body.title)
    await interviews.set_title(interview.id, body.title)
    await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_RENAMED)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(interview_id: UUID, user: CurrentUser) -> None:
    """Credits, results and questions go first, so a failure leaves the interview to delete
    again."""
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancel the generation instead")

    # Settled while rounds still has the answers. Released again as it's removed, for an invite
    # made or sent again meanwhile; a charged candidate stays charged.
    await settle_removed(await invites.unfinished(interview.id))
    await rounds.delete_interview_data(interview.set_id)
    await library.delete_interview(interview.set_id)
    await release_unfinished(await interviews.remove(interview.id))
    await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_DELETED)


@router.post("/{interview_id}/preview", status_code=status.HTTP_201_CREATED)
async def preview_interview(interview_id: UUID, user: CurrentUser) -> PreviewOut:
    """A company member takes their own test as a candidate would: free, kept out of the
    candidate list, and its answers out of the questions' statistics. Each preview is new."""
    await refuse_if_paused(get_redis(), "preview", user_id=user.uid)
    interview, _, _ = await interview_for(user, interview_id)
    await hit(
        get_redis(),
        f"rate:previews:{user.uid}",
        "PREVIEWS_PER_USER_HOUR",
        company_id=interview.company_id,
        user_id=user.uid,
    )
    interview = await attach_set(interview)
    content = await library.get_content(interview.set_id) if interview.set_id else None

    if content is None or not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview is not ready yet")

    # No invite stands behind a preview, so finishing it charges nothing.
    created = await rounds.create_sessions(
        {
            "user_id": user.uid,
            "candidate_invite_id": str(uuid4()),
            "question_seconds": interview.question_seconds,
            "topics": session_topics(interview, content, await multi_share(get_redis())),
            "preview": True,
        }
    )
    await track("interview_previewed", user_id=user.uid, company_id=interview.company_id)

    return PreviewOut(session_id=created[0]["id"])
