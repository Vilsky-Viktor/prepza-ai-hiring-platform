from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.constants.notifications import MAX_COMPANIES_PER_CALL


class CandidateUpdatesIn(BaseModel):
    company_ids: list[UUID] = Field(max_length=MAX_COMPANIES_PER_CALL)
    since: AwareDatetime
    until: AwareDatetime


class CandidateUpdateOut(BaseModel):
    """One candidate's step: `kind` is candidate_started, candidate_finished (with the grade and
    whether it reached the interview's pass mark) or invite_undelivered; `link` is their page."""

    kind: str
    at: datetime
    company_id: UUID
    interview_id: UUID
    title: str | None
    invite_id: UUID
    email: str
    candidate_name: str | None
    grade: int | None = None
    passed: bool | None = None
    link: str


class CandidateUpdatesOut(BaseModel):
    """The newest MAX_UPDATES steps, and how many of each kind there were in all (`passed`:
    the finished who passed)."""

    items: list[CandidateUpdateOut]
    counts: dict[str, int]
