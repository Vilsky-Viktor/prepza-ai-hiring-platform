from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from prepza_common.config.constants import MAX_ADJUSTMENT, MAX_ADJUSTMENT_NOTE
from pydantic import BaseModel, Field, StringConstraints

from companies.constants.superadmin import MAX_SUPPORT_QUERY, SupportKind
from companies.constants.verification import VerificationStatus


class SupportSearchIn(BaseModel):
    """A link or path from prepza's site, an id (an account's, a company's, an interview's, a
    candidate's or a Paddle transaction's), an email address, or part of a company's name."""

    query: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_SUPPORT_QUERY)
    ]


class SupportResultOut(BaseModel):
    """An account (its id the account's, its title the account's address), or a company, an
    interview or a candidate (an invite, its title the candidate's email) with the company it
    belongs to; an account belongs to none."""

    kind: SupportKind
    id: str
    title: str
    company_id: UUID | None = None
    company_name: str | None = None


class SupportSearchOut(BaseModel):
    results: list[SupportResultOut]


class SupportMemberOut(BaseModel):
    """An owner, admin or viewer; `user_id` is None until an invited one joins."""

    email: str
    role: str
    user_id: str | None


class SupportCompanyOut(BaseModel):
    """A company as support sees it: its people, and its credits (`reserved` is set aside for
    candidates who haven't finished)."""

    id: UUID
    name: str
    verification_status: VerificationStatus
    verified_domain: str | None
    suspended: bool
    created_at: datetime
    members: list[SupportMemberOut]
    balance: int
    reserved: int


class SupportAdjustmentIn(BaseModel):
    """Credits a superadmin adds (positive) or removes (negative), with the reason the company's
    history shows; `key` makes a repeated request count once."""

    amount: int = Field(ge=-MAX_ADJUSTMENT, le=MAX_ADJUSTMENT)
    note: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_ADJUSTMENT_NOTE)
    ]
    key: UUID


class SupportUserCompanyOut(BaseModel):
    """A company the account is a member of, with its role there."""

    id: UUID
    name: str
    role: str


class SupportTopUpOut(BaseModel):
    """A top-up the account paid for into a company: `total` in minor units, tax included;
    `company_name` None once the company is deleted."""

    transaction_id: str
    company_id: UUID
    company_name: str | None
    total: str
    currency: str
    created_at: datetime


class SupportUserOut(BaseModel):
    """An account as support sees it: `email` and `created_at` None once the account is gone
    (its memberships may outlive it), or when its sign-in has none."""

    user_id: str
    email: str | None
    created_at: datetime | None
    companies: list[SupportUserCompanyOut]
    top_ups: list[SupportTopUpOut]


class SupportSignalsOut(BaseModel):
    """How many integrity signals the candidate gave: page leaves, copy attempts and answers
    picked too fast to have read."""

    tab_leaves: int
    copies: int
    fast_answers: int


class SupportCandidateOut(BaseModel):
    """A candidate as support sees them, without their questions or answers. `extra_time` is a
    percentage of each question's time; `credits` says whether billing holds, charged or gave
    back their credits (None when it never held any)."""

    invite_id: UUID
    email: str
    name: str | None
    status: str
    company_id: UUID
    company_name: str
    interview_id: UUID
    interview_title: str | None
    invited_at: datetime
    last_sent_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    grade: int | None
    passed: bool | None
    extra_time: int
    signals: SupportSignalsOut
    credits: Literal["held", "charged", "released"] | None


class SupportInterviewOut(BaseModel):
    """An interview as support sees it: its topics by name, never its questions."""

    id: UUID
    title: str | None
    status: str
    company_id: UUID
    company_name: str
    created_at: datetime
    generation_id: UUID | None
    generation_failed: bool
    topics: list[str]
    question_seconds: int
    pass_mark: int
    candidate_count: int


class SupportCandidateRowOut(BaseModel):
    """A row of an interview's candidates."""

    invite_id: UUID
    email: str
    name: str | None
    status: str
    grade: int | None
    created_at: datetime
