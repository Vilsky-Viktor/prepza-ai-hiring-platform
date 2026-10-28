from uuid import UUID, uuid5

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams
from prepza_common.limits.pause import refuse_if_paused

from library.constants.sets import SetKind
from library.integrations import generation
from library.integrations.redis import get_redis
from library.repositories import feedback, preparations, quality, quality_report
from library.schemas.feedback import ReportOut
from library.schemas.quality_report import FlaggedQuestionOut, ReplacedQuestionOut

# The admin zone's quality tab: what's flagged now, and what was replaced.
router = APIRouter(prefix="/superadmin/quality", tags=["superadmin"])


@router.get("/flagged")
async def list_flagged(superadmin: SuperadminUser, page: PageParams) -> list[FlaggedQuestionOut]:
    return [
        FlaggedQuestionOut(
            question_id=question.id,
            text=question.text,
            options=question.options,
            flag=stats.flag,
            actionable=question_set.kind == SetKind.TEMPLATE,
            answers=stats.answers,
            correct=stats.correct,
            reports=reports,
            set_title=question_set.title,
            set_kind=question_set.kind,
            at=stats.updated_at,
        )
        for question, stats, question_set, reports in await quality_report.flagged(
            page.offset, page.limit
        )
    ]


@router.get("/replaced")
async def list_replaced(
    superadmin: SuperadminUser, page: PageParams, after: UUID | None = None
) -> list[ReplacedQuestionOut]:
    """Newest first, a page after the revision `after` (the last one shown): paged by key, as the
    list grows across every company."""
    return [
        ReplacedQuestionOut(
            revision_id=revision.id,
            question_id=revision.question_id,
            text=revision.text,
            options=revision.options,
            answers=revision.answers,
            correct=revision.correct,
            reports=len(revision.reports),
            set_title=question_set.title,
            set_kind=question_set.kind,
            at=revision.replaced_at,
            new_text=new_text,
            new_options=new_options,
        )
        for revision, question_set, (new_text, new_options) in await quality_report.replaced(
            after, page.limit
        )
    ]


async def flagged_template_question(question_id: UUID) -> str:
    """A flagged question in a template, or not found; its flag."""
    question_set = await preparations.get_for_question(question_id)
    found = await quality.load(question_id)

    if question_set is None or question_set.kind != SetKind.TEMPLATE or found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    stats = found[1]

    if stats is None or stats.flag is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Question isn't flagged")

    return stats.flag


@router.post("/{question_id}/fix", status_code=status.HTTP_202_ACCEPTED)
async def fix_now(question_id: UUID, superadmin: SuperadminUser) -> None:
    """Sends the question to the verifier at once; it fixes or replaces it in the background."""
    await refuse_if_paused(get_redis(), "question_fix", user_id=superadmin.uid)
    flag = await flagged_template_question(question_id)
    await generation.verify_question(question_id, flag, now=True)


@router.post("/{question_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss(question_id: UUID, superadmin: SuperadminUser) -> None:
    """The flag is wrong: the question stays, and isn't flagged again until it changes."""
    await flagged_template_question(question_id)
    await quality.save_flag(question_id, None, kept=True)


@router.get("/{question_id}/reports")
async def list_reports(
    question_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ReportOut]:
    """A flagged question's reports, newest first."""
    reports = await feedback.list_reports(question_id, page.offset, page.limit)

    return [ReportOut.model_validate(report, from_attributes=True) for report in reports]


@router.get("/revisions/{revision_id}/reports")
async def list_revision_reports(
    revision_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ReportOut]:
    """The reports a replaced question had, as kept with its old content, newest first."""
    found = await quality_report.revision(revision_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Revision not found")

    newest = sorted(found.reports, key=lambda report: report["created_at"], reverse=True)

    return [
        # Kept reports have no id of their own; their place in the revision names them.
        ReportOut(id=uuid5(revision_id, str(index)), **report)
        for index, report in enumerate(newest)
    ][page.offset : page.offset + page.limit]
