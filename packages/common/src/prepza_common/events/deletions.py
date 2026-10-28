"""The payloads of companies' deletion events, which the holders of a company's or an
interview's data (rounds, library, ats) consume to delete their own copies. Consumers ignore
fields they don't know (tolerant reader); a payload that fails validation can never be handled
(a ValueError: handle_or_drop drops it)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

INTERVIEW_DELETED = "interview.deleted"
COMPANY_DELETED = "company.deleted"


class InterviewDeleted(BaseModel):
    """An interview went: its questions' set (none while it was still generating) and its
    generation, so each holder finds what it keeps by its own key."""

    model_config = ConfigDict(extra="ignore")

    interview_id: UUID
    company_id: UUID
    set_id: UUID | None = None
    generation_id: UUID | None = None


class CompanyDeleted(BaseModel):
    """A company went, with every interview and candidate of it."""

    model_config = ConfigDict(extra="ignore")

    company_id: UUID
