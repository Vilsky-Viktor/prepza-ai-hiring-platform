from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.limits.rate_limit import hit, hit_emails

from app.constants.reports import (
    NO_FINISHED_CANDIDATES,
    NOT_A_PDF,
    OUTSIDE_COMPANY,
    TOO_MANY_REPORT_EMAILS,
)
from app.constants.roles import EDITORS
from app.helpers.reports import is_report_pdf
from app.integrations.redis import get_redis
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.storage import candidates


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

    if not await candidates.any_finished(interview.id):
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
