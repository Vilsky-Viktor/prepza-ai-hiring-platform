from datetime import datetime

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
    # Running, but nothing is charged until the card is updated.
    paused: bool = False
    product: str | None
    threshold: int | None
    products: list[str]
    thresholds: list[int]
    # Each top-up's price (minor units) in `currency`, the company's; the chosen one at what
    # each charge costs now.
    currency: str
    prices: dict[str, int]
    # A new price announced for the chosen top-up, and the day charges cost it from.
    next_price: int | None = None
    next_price_from: datetime | None = None
    checkout: CheckoutOut | None = None
