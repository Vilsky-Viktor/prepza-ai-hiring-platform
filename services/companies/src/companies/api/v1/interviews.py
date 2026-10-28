from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams
from prepza_common.events.analytics import track
from prepza_common.events.audit_actions import AuditAction
from prepza_common.limits.limits import question_seconds
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit_or_skip

from companies.api.dependencies import Via
from companies.constants.interviews import SETTINGS_LOGGED
from companies.constants.invites import INTERVIEW_NOT_READY, MAX_SEARCH_LENGTH
from companies.helpers.interviews import (
    attach_set,
    attach_set_if_reachable,
    interview_minutes,
    interview_out,
    interview_questions,
    interviews_page,
    session_topics,
    topics_out,
)
from companies.integrations import library, rounds
from companies.integrations.redis import get_redis
from companies.repositories import audit, candidates, interviews
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
from companies.services import interview_creation, set_cache
from companies.services.access import (
    can_edit,
    refuse_without_pledge,
    require_company,
    require_editor,
)
from companies.services.candidate_billing import release_unfinished, settle_unfinished
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
    key = f"rate:template-copies:{company.id}"
    who = {"company_id": company.id, "user_id": user.uid}
    await hit_or_skip(get_redis(), key, "TEMPLATE_COPIES_PER_HOUR", **who)
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
        language=interview.language,
        topics=topics,
        total_minutes=interview_minutes(found, interview.topic_limits, interview.question_seconds),
        total_questions=interview_questions(found, interview.topic_limits),
        can_edit=can_edit(member),
        keep_private=interview.keep_private,
    )


@router.patch("/{interview_id}/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_settings(
    interview_id: UUID, body: InterviewSettings, user: CurrentUser, via: Via
) -> None:
    interview, _, _ = await interview_for(user, interview_id, editor=True)
    await interviews.update_settings(interview.id, body)
    sent = body.model_dump(include=SETTINGS_LOGGED, exclude_none=True)

    if any(value != getattr(interview, key) for key, value in sent.items()):
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
    await settle_unfinished(interview.id)
    await rounds.delete_interview_data(interview.set_id)
    await library.delete_interview(interview.set_id)
    await release_unfinished(await interviews.remove(interview.id))
    await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_DELETED)


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
    interview = await attach_set(interview)
    content = await library.get_content(interview.set_id) if interview.set_id else None

    if content is None or not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview is not ready yet")

    # Counted once it would start (a test not ready yet isn't a preview), against floods: with
    # Redis down, not counted rather than refused.
    await hit_or_skip(
        get_redis(),
        f"rate:previews:{user.uid}",
        "PREVIEWS_PER_USER_HOUR",
        company_id=interview.company_id,
        user_id=user.uid,
    )

    # No invite stands behind a preview, so finishing it charges nothing.
    created = await rounds.create_sessions(
        {
            "user_id": user.uid,
            "company_id": str(interview.company_id),
            "candidate_invite_id": str(uuid4()),
            "question_seconds": interview.question_seconds,
            "topics": session_topics(interview, content, await multi_share(get_redis())),
            "preview": True,
        }
    )
    await track("interview_previewed", user_id=user.uid, company_id=interview.company_id)

    return PreviewOut(session_id=created[0]["id"])
