from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from companies.constants.verification import (
    MAX_DECLINE_REASON_LENGTH,
    MAX_WEBSITE_LENGTH,
    VerificationStatus,
)


class WebsiteIn(BaseModel):
    """The company's website as typed; empty removes it, and the verification with it."""

    website: str = Field(default="", max_length=MAX_WEBSITE_LENGTH)


class VerificationOut(BaseModel):
    website_domain: str | None
    # Set once a superadmin approved the company (the badge).
    verified_domain: str | None
    verification_status: VerificationStatus
    # Why a superadmin declined it, when they said.
    decline_reason: str | None = None


class ApproveIn(BaseModel):
    """The name and domain the superadmin reviewed; approved only if the request still has them."""

    name: str
    domain: str


class DeclineIn(BaseModel):
    reason: str = Field(default="", max_length=MAX_DECLINE_REASON_LENGTH)


class VerificationRequestOut(BaseModel):
    """A company sent for review, for the superadmin: the name and domain to check, the work
    email that proved the domain, and the decision once made."""

    company_id: UUID
    name: str
    domain: str
    email: str | None
    status: VerificationStatus
    submitted_at: datetime | None
    decided_at: datetime | None
    decline_reason: str | None
