from datetime import datetime
from uuid import UUID

from prepza_common.constants import MAX_ADJUSTMENT, MAX_ADJUSTMENT_NOTE, MAX_PAGE_SIZE
from pydantic import BaseModel, Field

from app.constants.payment_failures import PaymentFailure


class TopUpOut(BaseModel):
    key: str
    title: str
    price_cents: int
    credits: int
    # The whole candidates it buys, and what each costs at its volume price.
    candidates: int
    candidate_cents: int
    price_id: str | None


class CandidatePriceOut(BaseModel):
    """A candidate's price when credits are bought in a top-up from this many dollars."""

    from_dollars: int
    cents: int


class CandidateTierOut(BaseModel):
    """A candidate's price in a top-up of any number of candidates, from this many. From
    `upgrade_from` candidates on, the top-up buys the next tier's smallest one instead, which
    costs no more (none for the last tier)."""

    from_candidates: int
    cents: int
    upgrade_from: int | None


class CustomTopUpOut(BaseModel):
    """A top-up of any number of candidates, from `min_candidates` to `max_candidates`, each at
    its tier's price, smallest first."""

    min_candidates: int
    max_candidates: int
    # Not while Paddle's product for it isn't set.
    on_sale: bool
    tiers: list[CandidateTierOut]


class CatalogOut(BaseModel):
    """What the pricing page and Paddle.js need. Prices are decided here, not in the client."""

    environment: str
    client_token: str
    currency: str
    candidate_credits: int
    # A candidate's price at each volume tier, cheapest last.
    candidate_prices: list[CandidatePriceOut]
    # The cheapest and the standard price of a candidate, for "$2–5 per candidate".
    candidate_cents_min: int
    candidate_cents_max: int
    welcome_company: int
    # The candidates a new company's welcome credits cover.
    free_candidates: int
    referral_company: int
    products: list[TopUpOut]
    custom: CustomTopUpOut


class BalanceOut(BaseModel):
    balance: int
    reserved: int
    available: int
    # Running low: time to suggest a top-up.
    low: bool
    # Candidates the available credits pay for.
    candidates: int = 0


class PaidOut(BaseModel):
    # Whether the company ever topped up: a paying customer isn't held to free accounts' limits.
    paid: bool


class LowCompanyOut(BaseModel):
    company_id: str
    available: int
    # Candidates the available credits pay for.
    candidates: int = 0


class LowCompaniesOut(BaseModel):
    companies: list[LowCompanyOut]


class AdjustmentIn(BaseModel):
    """A superadmin's adjustment of a company's credits: `amount` adds (positive) or removes
    (negative); `note` says why, as the company's history shows it; `key` makes a repeated
    request count once."""

    amount: int = Field(ge=-MAX_ADJUSTMENT, le=MAX_ADJUSTMENT)
    note: str = Field(min_length=1, max_length=MAX_ADJUSTMENT_NOTE)
    key: UUID


class OwnersIn(BaseModel):
    owner_ids: list[str] = Field(max_length=MAX_PAGE_SIZE)


class TopUpCheckoutIn(BaseModel):
    """A top-up of this many candidates; billing checks the count and sets the price."""

    candidates: int


class TopUpCheckoutOut(BaseModel):
    """The Paddle transaction the checkout opens."""

    transaction_id: str


class WelcomeIn(BaseModel):
    owner_email: str
    # The code of the link the owner came through, and their other companies, which can't
    # refer this one.
    referral: str | None = None
    related: list[str] = Field(default=[], max_length=MAX_PAGE_SIZE)


class ReferralRewardOut(BaseModel):
    """A company that came through the link and topped up, so both got the reward."""

    company_id: str
    rewarded_at: datetime
    # The credits it gave the referrer then (0 over the yearly limit).
    credits: int


class ReferralOut(BaseModel):
    """The owner's referral link code, what it earns, and how many it has earned for."""

    code: str
    reward: int
    rewarded: int
    # The latest rewards, newest first.
    rewards: list[ReferralRewardOut]


class AutoTopUpIn(BaseModel):
    """Which top-up to buy, and under which available balance (credits)."""

    product: str
    threshold: int


class CheckoutOut(BaseModel):
    """The Paddle checkout to open: its price and the custom data to send with it."""

    price_id: str
    custom_data: dict[str, str]


class AutoTopUpOut(BaseModel):
    """A wallet's automatic top-up: whether it's offered at all, running, or waiting for its
    checkout, what it buys and when, and the choices."""

    offered: bool
    on: bool
    waiting: bool
    product: str | None
    threshold: int | None
    products: list[str]
    thresholds: list[int]
    # Only when turning it on still needs the checkout that saves the card.
    checkout: CheckoutOut | None = None


class HistoryEntryOut(BaseModel):
    """One movement of a wallet's credits. `total` (minor units, tax included) and `currency`
    are what a top-up cost or an adjustment moved, when known; `transaction_id` is the Paddle
    transaction of a top-up or adjustment, and `hold_key` the key of a candidate's credits."""

    id: UUID
    amount: int
    reason: str
    created_at: datetime
    total: str | None
    currency: str | None
    automatic: bool
    transaction_id: str | None
    hold_key: str | None
    # A superadmin's adjustment: why.
    note: str | None = None


class PurchaseOwnerOut(BaseModel):
    """Whose wallet a top-up's transaction paid into."""

    owner_type: str
    owner_id: str


class InvoiceOut(BaseModel):
    """A temporary link to the transaction's invoice PDF."""

    url: str


class BuyerPurchaseOut(BaseModel):
    """A top-up someone paid for into a company: `total` in minor units, tax included."""

    transaction_id: str
    company_id: str
    total: str
    currency: str
    created_at: datetime


class HoldOut(BaseModel):
    """Credits set aside for one piece of work: open, charged or released."""

    status: str


class PaymentFailureOut(BaseModel):
    """Why a checkout's latest payment failed, as one of a fixed set; the site says what the buyer
    can do for each."""

    reason: PaymentFailure = Field(description="Why the payment failed, by what the buyer can do.")
