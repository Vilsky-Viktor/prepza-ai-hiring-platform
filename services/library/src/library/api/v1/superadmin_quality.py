from uuid import UUID, uuid5

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams

from library.constants.sets import SetKind
from library.core.db import Session
from library.repositories import feedback, quality_report
from library.schemas.feedback import ReportOut
from library.schemas.quality_report import FlaggedQuestionOut, ReplacedQuestionOut
from library.services import admin_quality

# The admin zone's quality tab: what's flagged now, and what was replaced.
router = APIRouter(prefix="/superadmin/quality", tags=["superadmin"])


@router.get("/flagged")
async def list_flagged(superadmin: SuperadminUser, page: PageParams) -> list[FlaggedQuestionOut]:
    async with Session() as session:
        rows = await quality_report.flagged(session, page.offset, page.limit)

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
        for question, stats, question_set, reports in rows
    ]


@router.get("/replaced")
async def list_replaced(
    superadmin: SuperadminUser, page: PageParams, after: UUID | None = None
) -> list[ReplacedQuestionOut]:
    """Newest first, a page after the revision `after` (the last one shown): paged by key, as the
    list grows across every company."""
    async with Session() as session:
        rows = await quality_report.replaced(session, after, page.limit)

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
        for revision, question_set, (new_text, new_options) in rows
    ]


@router.post("/{question_id}/fix", status_code=status.HTTP_202_ACCEPTED)
async def fix_now(question_id: UUID, superadmin: SuperadminUser) -> None:
    """Sends the question to the verifier at once; it fixes or replaces it in the background."""
    await admin_quality.fix_now(question_id, superadmin.uid)


@router.post("/{question_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss(question_id: UUID, superadmin: SuperadminUser) -> None:
    """The flag is wrong: the question stays, and isn't flagged again until it changes."""
    await admin_quality.dismiss(question_id)


@router.get("/{question_id}/reports")
async def list_reports(
    question_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ReportOut]:
    """A flagged question's reports, newest first."""
    async with Session() as session:
        reports = await feedback.list_reports(session, question_id, page.offset, page.limit)

    return [ReportOut.model_validate(report, from_attributes=True) for report in reports]


@router.get("/revisions/{revision_id}/reports")
async def list_revision_reports(
    revision_id: UUID, superadmin: SuperadminUser, page: PageParams
) -> list[ReportOut]:
    """The reports a replaced question had, as kept with its old content, newest first."""
    async with Session() as session:
        found = await quality_report.revision(session, revision_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Revision not found")

    newest = sorted(found.reports, key=lambda report: report["created_at"], reverse=True)

    return [
        # Kept reports have no id of their own; their place in the revision names them.
        ReportOut(id=uuid5(revision_id, str(index)), **report)
        for index, report in enumerate(newest)
    ][page.offset : page.offset + page.limit]
