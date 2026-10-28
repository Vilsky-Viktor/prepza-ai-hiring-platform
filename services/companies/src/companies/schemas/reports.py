from pydantic import BaseModel, EmailStr, Field

from companies.constants.reports import MAX_REPORT_BYTES
from companies.schemas.invites import CandidateOut


class ReportEmailIn(BaseModel):
    """Who gets the candidate's report, and the PDF the page made, base64-encoded."""

    email: EmailStr
    pdf: str = Field(min_length=1, max_length=MAX_REPORT_BYTES * 4 // 3 + 4)


class InterviewReportOut(BaseModel):
    """Every candidate of a test with their totals, as its candidates tab lists them, for the
    test's PDF report: best grade first."""

    title: str | None
    company: str
    logo_url: str | None
    verified_domain: str | None
    pass_mark: int
    candidates: list[CandidateOut]
