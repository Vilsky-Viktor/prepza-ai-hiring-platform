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


class TopUpCheckoutIn(BaseModel):
    """A top-up of this many candidates; billing checks the count and sets the price."""

    candidates: int


class TopUpCheckoutOut(BaseModel):
    """The Paddle transaction the checkout opens."""

    transaction_id: str


class InvoiceOut(BaseModel):
    """A temporary link to the invoice PDF."""

    url: str


class PaymentFailureOut(BaseModel):
    """Why a checkout's latest payment failed, as billing decides it: one of card_declined,
    insufficient_funds, expired_card, invalid_details, authentication_failed, card_not_supported,
    payment_method_failed, try_later or other. The site says what the buyer can do for each."""

    reason: str
