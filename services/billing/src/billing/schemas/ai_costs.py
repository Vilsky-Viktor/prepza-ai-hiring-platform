from datetime import date

from pydantic import BaseModel


class SpendOut(BaseModel):
    spend: float
    calls: int


class TotalsOut(SpendOut):
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int


class CategoryOut(SpendOut):
    category: str
    # Of the period's spend, 0 to 1.
    share: float


class ActionOut(SpendOut):
    action: str
    # Interviews, messages, questions... (minutes for transcription), and what one cost.
    units: float
    unit_cost: float
    paid_spend: float
    # Unpaid companies and people without a company.
    unpaid_spend: float


class ModelOut(TotalsOut):
    model: str
    # Of its input tokens, the share read from OpenAI's cache, 0 to 1.
    cached_share: float


class SpenderOut(SpendOut):
    id: str
    # The company's name or the account's email, when known.
    name: str | None


class DayOut(BaseModel):
    # The day, or the month's first day when the period is a year or all time.
    day: date
    spend: float


class MonthOut(BaseModel):
    spend: float
    # The monthly budget; 0 when none is set.
    budget: float
    share: float


class UnpaidTodayOut(BaseModel):
    spend: float
    cap: float
    share: float


class AiCostsOut(BaseModel):
    totals: TotalsOut
    month: MonthOut
    unpaid_today: UnpaidTodayOut
    categories: list[CategoryOut]
    actions: list[ActionOut]
    models: list[ModelOut]
    companies: list[SpenderOut]
    users: list[SpenderOut]
    # By day for a month, by month for a year or all time.
    by_month: bool
    days: list[DayOut]


class AiSpendOut(SpendOut):
    """A company's or user's AI spend over the last SPEND_DAYS days, for its support page."""

    days: int
