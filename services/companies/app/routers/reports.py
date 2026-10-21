from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import CurrentUser
from prepza_common.rate_limit import recipient_key

from app.constants.invites import InviteStatus
from app.constants.reports import READ_BATCH
from app.helpers.candidates import candidate_label, candidate_out
from app.helpers.interviews import interview_title
from app.helpers.logos import logo_path
from app.helpers.reports import report_sender
from app.integrations import rounds
from app.schemas.reports import InterviewReportOut, ReportEmailIn
from app.service_auth import Via
from app.services import candidate_results
from app.services import outbox as outbox_service
from app.services.interview_access import candidate_for, interview_for
from app.services.report_emails import allow_report_email
from app.storage import audit, candidates, reports

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

    if invite.status == InviteStatus.DELETED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    email = str(body.email).lower()
    recipient = f"report:{invite.id}:{recipient_key(email)}"
    await allow_report_email(user, company, member, interview, body.pdf, email, recipient)
    await reports.queue_email(
        {
            "email": email,
            **report_sender(user, interview),
            "company": company.name,
            "title": await interview_title(interview) or "",
            "candidate": candidate_label(invite),
            "pdf": body.pdf,
        }
    )
    await audit.record(
        company.id,
        user.uid,
        AuditAction.REPORT_EMAILED,
        invite.id,
        via=via,
        target_kind=TargetKind.CANDIDATE,
    )
    await outbox_service.flush_quietly()


@router.get("/{interview_id}/report")
async def interview_report(interview_id: UUID, user: CurrentUser) -> InterviewReportOut:
    interview, company, _ = await interview_for(user, interview_id)
    await candidate_results.backfill(interview.id)
    every, totals = [], {}

    # A batch at a time, with its candidates' scores, until one comes up short.
    while True:
        batch = await candidates.for_report(interview.id, len(every), READ_BATCH)
        every += batch
        totals |= await rounds.invite_scores([invite.id for invite in batch])

        if len(batch) < READ_BATCH:
            break

    return InterviewReportOut(
        title=await interview_title(interview),
        company=company.name,
        logo_url=logo_path(company),
        verified_domain=company.verified_domain,
        pass_mark=interview.pass_mark,
        candidates=[
            candidate_out(invite, totals.get(str(invite.id)) or {}, interview) for invite in every
        ],
    )


@router.post("/{interview_id}/report/email", status_code=status.HTTP_202_ACCEPTED)
async def email_interview_report(
    interview_id: UUID, body: ReportEmailIn, user: CurrentUser, via: Via
) -> None:
    """Emails the test's candidates report, made on its candidates tab, like a candidate's."""
    interview, company, member = await interview_for(user, interview_id)

    email = str(body.email).lower()
    recipient = f"report:{interview.id}:{recipient_key(email)}"
    await allow_report_email(user, company, member, interview, body.pdf, email, recipient)
    title = await interview_title(interview) or ""
    await reports.queue_email(
        {
            "kind": "candidates",
            "email": email,
            **report_sender(user, interview),
            "company": company.name,
            "title": title,
            "pdf": body.pdf,
        }
    )
    await audit.record_interview(interview, user.uid, AuditAction.REPORT_EMAILED, via)
    await outbox_service.flush_quietly()
