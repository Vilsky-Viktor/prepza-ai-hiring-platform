"""The payloads of the deletion events, which the holders of a company's, an interview's or a
user's data consume to delete their own copies: companies' (rounds, library, ats and others) and
accounts' `user.deleted`. Consumers ignore
fields they don't know (tolerant reader); a payload that fails validation can never be handled
(a ValueError: handle_or_drop drops it)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

INTERVIEW_DELETED = "interview.deleted"
COMPANY_DELETED = "company.deleted"
USER_DELETED = "user.deleted"


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


class UserDeleted(BaseModel):
    """A user deleted their account: each holder deletes what it keeps under their id, and
    under their email what it keeps about them as a candidate. Companies has already deleted its
    part (it may refuse, so accounts calls it first); accounts sends it again after a restore
    (its erasures), so a holder deletes whatever a backup brought back."""

    model_config = ConfigDict(extra="ignore")

    user_id: str
    email: str
