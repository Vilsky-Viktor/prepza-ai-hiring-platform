from pydantic import BaseModel


class AutoTopUpIn(BaseModel):
    """Which top-up to buy, and under which available balance (credits)."""

    product: str
    threshold: int


class CheckoutOut(BaseModel):
    """The Paddle transaction the checkout opens, made by billing in the company's currency."""

    transaction_id: str


class AutoTopUpOut(BaseModel):
    """The company's automatic top-up, as billing has it."""

    offered: bool
    on: bool
    waiting: bool
    product: str | None
    threshold: int | None
    products: list[str]
    thresholds: list[int]
    # Each top-up's price (minor units) in `currency`: a running one's, or else the company's.
    currency: str
    prices: dict[str, int]
    checkout: CheckoutOut | None = None
