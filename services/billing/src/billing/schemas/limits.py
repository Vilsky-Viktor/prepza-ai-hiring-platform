from datetime import datetime

from pydantic import BaseModel, Field


class HitterOut(BaseModel):
    id: str
    name: str | None
    hits: int


class LimitHitsOut(BaseModel):
    limit: str
    # "ours" or "provider:<name>".
    kind: str
    scope: str
    # The current value; None for a provider's limit or the pause.
    value: float | None
    unit: str | None
    window: int | None
    hits: int
    companies: list[HitterOut]
    users: list[HitterOut]


class LimitHitListsOut(BaseModel):
    ours: list[LimitHitsOut]
    providers: list[LimitHitsOut]


class LimitOut(BaseModel):
    name: str
    service: str
    value: float
    default: float
    changed: bool
    unit: str
    window: int | None
    lowest: float
    highest: float
    scope: str
    audience: str | None
    # False for a plain value (testee_common.limits.limit_types): nothing counts against it, so it has
    # no window and no hits.
    counted: bool
    # Hits in the last HITS_DAYS days.
    hits: int
    # The unpaid counterpart, shown beside it.
    unpaid: "LimitOut | None" = None


class ProviderLimitOut(BaseModel):
    name: str
    provider: str
    hits: int


class LimitsOut(BaseModel):
    limits: list[LimitOut]
    providers: list[ProviderLimitOut]
    hits_days: int


class LimitIn(BaseModel):
    # 0 only where the limit's bounds allow it (a share of none).
    value: float = Field(ge=0)


class LimitChangeOut(BaseModel):
    name: str
    old_value: float | None
    new_value: float | None
    changed_by_email: str
    changed_at: datetime
