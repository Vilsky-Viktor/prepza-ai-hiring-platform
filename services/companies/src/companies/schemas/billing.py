from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreditCandidateOut(BaseModel):
    """The candidate whose invite set credits aside or was charged for, and their interview."""

    invite_id: UUID
    interview_id: UUID
    email: str
    name: str | None
    interview_title: str | None


class HistoryEntryOut(BaseModel):
    """One movement of the company's credits: `amount` is signed, `reason` says what it was.
    `total` (minor units, tax included) and `currency` are the money a top-up cost or a refund
    or chargeback moved, when known. `invoice_id` is the top-up's transaction, whose invoice
    can be opened. A candidate's charge names the candidate, or `candidate_deleted` when their
    invite is gone."""

    id: UUID
    amount: int
    reason: str
    created_at: datetime
    total: str | None
    currency: str | None
    automatic: bool
    invoice_id: str | None
    candidate: CreditCandidateOut | None
    candidate_deleted: bool
    # Why a superadmin adjusted the credits (reason "adjustment").
    note: str | None = None


class InvoiceOut(BaseModel):
    """A temporary link to the invoice PDF."""

    url: str
