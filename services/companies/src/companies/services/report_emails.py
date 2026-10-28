from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.limits.rate_limit import hit, hit_emails, recipient_key

from companies.constants.invites import InviteStatus
from companies.constants.reports import (
    NO_FINISHED_CANDIDATES,
    NOT_A_PDF,
    OUTSIDE_COMPANY,
    TOO_MANY_REPORT_EMAILS,
)
from companies.constants.roles import EDITORS
from companies.core.db import Session
from companies.helpers.candidates import candidate_label
from companies.helpers.reports import is_report_pdf, report_sender
from companies.integrations.redis import get_redis
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import audit, candidates, reports
from companies.services import outbox as outbox_service
from companies.services.interview_views import interview_title


def inside_company(company: Company, email: str) -> bool:
    """Whether `email` (lowercased) is the address of one of the company's joined members."""
    return any(
        member.user_id and member.invited_email.lower() == email for member in company.members
    )


async def allow_report_email(
    user: User,
    company: Company,
    member: Member,
    interview: Interview,
    pdf: str,
    email: str,
    recipient: str,
) -> None:
    """Refuses a report email from a viewer to `email` (lowercased) outside the company's
    members (403), and unless a candidate finished the interview and the PDF is one; then counts
    it towards the member's email limits and the company's daily reports."""
    if member.role not in EDITORS and not inside_company(company, email):
        raise HTTPException(status.HTTP_403_FORBIDDEN, OUTSIDE_COMPANY)

    async with Session() as session:
        finished = await candidates.any_finished(session, interview.id)

    if not finished:
        raise HTTPException(status.HTTP_409_CONFLICT, NO_FINISHED_CANDIDATES)

    if not is_report_pdf(pdf):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOT_A_PDF)

    redis = get_redis()
    await hit_emails(redis, user.uid, recipient, company.id)
    await hit(
        redis,
        f"rate:report-emails:day:{company.id}",
        "REPORT_EMAILS_PER_COMPANY_DAY",
        TOO_MANY_REPORT_EMAILS,
        company_id=company.id,
        user_id=user.uid,
    )


async def email_candidate_report(
    user: User,
    company: Company,
    member: Member,
    interview: Interview,
    invite: CandidateInvite,
    email: str,
    pdf: str,
    via: str | None,
) -> None:
    """Emails the candidate's PDF report to `email` (lowercased), as allow_report_email allows;
    the email and its line in the action log are saved together."""
    if invite.status == InviteStatus.DELETED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    recipient = f"report:{invite.id}:{recipient_key(email)}"
    await allow_report_email(user, company, member, interview, pdf, email, recipient)
    data = {
        "email": email,
        **report_sender(user, interview),
        "company": company.name,
        "title": await interview_title(interview) or "",
        "candidate": candidate_label(invite),
        "pdf": pdf,
    }

    async with Session.begin() as session:
        await reports.queue_email(session, data)
        await audit.record(
            session,
            company.id,
            user.uid,
            AuditAction.REPORT_EMAILED,
            invite.id,
            via=via,
            target_kind=TargetKind.CANDIDATE,
        )

    await outbox_service.flush_quietly()


async def email_interview_report(
    user: User,
    company: Company,
    member: Member,
    interview: Interview,
    email: str,
    pdf: str,
    via: str | None,
) -> None:
    """Emails the test's candidates report, like a candidate's: saved with its log line."""
    recipient = f"report:{interview.id}:{recipient_key(email)}"
    await allow_report_email(user, company, member, interview, pdf, email, recipient)
    data = {
        "kind": "candidates",
        "email": email,
        **report_sender(user, interview),
        "company": company.name,
        "title": await interview_title(interview) or "",
        "pdf": pdf,
    }

    async with Session.begin() as session:
        await reports.queue_email(session, data)
        await audit.record_interview(session, interview, user.uid, AuditAction.REPORT_EMAILED, via)

    await outbox_service.flush_quietly()
