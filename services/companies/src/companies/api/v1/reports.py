from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.auth import CurrentUser

from companies.api.dependencies import Via
from companies.schemas.reports import InterviewReportOut, ReportEmailIn
from companies.services import interview_reports, report_emails
from companies.services.interview_access import candidate_for, interview_for

router = APIRouter(prefix="/interviews", tags=["reports"])


@router.post(
    "/{interview_id}/candidates/{invite_id}/report/email", status_code=status.HTTP_202_ACCEPTED
)
async def email_report(
    interview_id: UUID, invite_id: UUID, body: ReportEmailIn, user: CurrentUser, via: Via
) -> None:
    """Emails the candidate's PDF report, made on their page, to someone such as a hiring
    manager (a viewer: only to one of the company's members). A reply goes to the member who sent
    it. Counts towards the member's email limits and the company's daily reports."""
    interview, invite, company, member = await candidate_for(user, interview_id, invite_id)
    await report_emails.email_candidate_report(
        user, company, member, interview, invite, str(body.email).lower(), body.pdf, via
    )


@router.get("/{interview_id}/report")
async def interview_report(interview_id: UUID, user: CurrentUser) -> InterviewReportOut:
    interview, company, _ = await interview_for(user, interview_id)

    return await interview_reports.report(interview, company)


@router.post("/{interview_id}/report/email", status_code=status.HTTP_202_ACCEPTED)
async def email_interview_report(
    interview_id: UUID, body: ReportEmailIn, user: CurrentUser, via: Via
) -> None:
    """Emails the test's candidates report, made on its candidates tab, like a candidate's."""
    interview, company, member = await interview_for(user, interview_id)
    await report_emails.email_interview_report(
        user, company, member, interview, str(body.email).lower(), body.pdf, via
    )
