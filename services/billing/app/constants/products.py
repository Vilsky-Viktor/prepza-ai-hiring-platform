from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from app.constants.credits import CANDIDATE_CREDITS

# The admin zone's support tab lists at most this many of a person's top-ups, newest first.
MAX_BUYER_PURCHASES = 100


class OwnerType(StrEnum):
    """Whose wallet; only companies have one."""

    COMPANY = "company"


@dataclass(frozen=True)
class TopUp:
    key: str
    title: str
    price_cents: int


# Fixed amounts; what each buys comes from helpers/credits.py.
# Each buys whole candidates at its own price: 10 at $5, 50 at $4, 200 at $3, 500 at $2.
TOP_UPS = [
    TopUp("topup_50", "$50", 5_000),
    TopUp("topup_200", "$200", 20_000),
    TopUp("topup_600", "$600", 60_000),
    TopUp("topup_1000", "$1,000", 100_000),
]

# What a candidate costs (in cents) when bought in a top-up from these amounts up (in cents),
# largest first: volume prices. Below them, a candidate costs CANDIDATE_CREDITS at
# CREDITS_PER_DOLLAR, $5; so larger top-ups buy more credits per dollar.
CANDIDATE_PRICE_TIERS = [(100_000, 200), (60_000, 300), (20_000, 400)]

# A top-up of any number of candidates: from the smallest top-up's candidates up to this many.
# Each candidate costs what it does in the largest top-up the count reaches (helpers/credits.py).
# Billing sells it as one item priced in the transaction itself (quantity 1, which the buyer
# can't change), with the candidates in its custom data under CUSTOM_TOP_UP_FLAG; the purchase
# is recorded as CUSTOM_TOP_UP_KEY.
CUSTOM_TOP_UP_MAX = 1_000
CUSTOM_TOP_UP_FLAG = "candidates"
CUSTOM_TOP_UP_KEY = "candidates"

CURRENCY = "USD"
# Paddle signs each webhook with a timestamp; older ones are refused, so a captured one can't be
# replayed later.
WEBHOOK_TOLERANCE_SECONDS = 5 * 60
# The only Paddle event that grants anything: a fully paid transaction.
TRANSACTION_COMPLETED = "transaction.completed"
# A transaction's origin when billing created it through Paddle's API (a checkout opened with
# items in the browser is "web").
PADDLE_API_ORIGIN = "api"
TOP_UP_UNAVAILABLE = "This top-up isn't available"
# Fixed text, so it's translated by its words: the range sold, from the smallest top-up's
# candidates to CUSTOM_TOP_UP_MAX (a test keeps them the same).
CANDIDATES_OUT_OF_RANGE = "Choose from 10 to 1,000 candidates."
# Refunds and chargebacks; a refund is approved after it's created, so both events matter.
ADJUSTMENT_EVENTS = ("adjustment.created", "adjustment.updated")
ADJUSTMENT_APPROVED = "approved"

# Automatic top-up: the balances (in credits) it can refill under, and the least time between two
# automatic charges, so a webhook still on its way can't cause a second one.
# They cover 1, 3 and 5 candidates.
AUTO_TOP_UP_THRESHOLDS = [CANDIDATE_CREDITS, 3 * CANDIDATE_CREDITS, 5 * CANDIDATE_CREDITS]
AUTO_TOP_UP_COOLDOWN = timedelta(minutes=10)
# A charge whose credits haven't come (its transaction.completed web hook late or failing, or a
# charge whose answer was lost) holds off the next one this long, so the card isn't charged again
# and again meanwhile.
AUTO_TOP_UP_UNCREDITED_WAIT = timedelta(days=1)
# After the card declines a charge, the next try (and its notice to the owner) waits this long,
# unless the automatic top-up is saved again first (say, after updating the card).
AUTO_TOP_UP_RETRY_AFTER = timedelta(days=1)
# Turning it on is a checkout for a $0 monthly subscription, which saves the card; Paddle tells
# us when it starts and when it ends (cancelled in Paddle, or after failed payments).
SUBSCRIPTION_CREATED = "subscription.created"
SUBSCRIPTION_CANCELED = "subscription.canceled"
# A subscription's status in Paddle once it has ended.
SUBSCRIPTION_ENDED_STATUS = "canceled"
# Marks the checkout that turns automatic top-up on.
AUTO_TOP_UP_FLAG = "auto_top_up"
# A running automatic top-up charges its buyer's card: only they change what it buys or when.
NOT_YOUR_AUTO_TOP_UP = (
    "Only the person whose card pays for it can change it. Turn it off, then turn it on with "
    "your own card."
)
PADDLE_API = {"sandbox": "https://sandbox-api.paddle.com", "production": "https://api.paddle.com"}
