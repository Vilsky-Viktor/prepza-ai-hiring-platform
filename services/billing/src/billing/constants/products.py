from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from billing.constants.credits import CANDIDATE_CREDITS
from billing.constants.currencies import Currency

# The admin zone's support tab lists at most this many of a person's top-ups, newest first.
MAX_BUYER_PURCHASES = 100


class OwnerType(StrEnum):
    """Whose wallet; only companies have one."""

    COMPANY = "company"


@dataclass(frozen=True)
class TopUp:
    # Kept as they were when each cost that many dollars: purchases and automatic top-ups store
    # them.
    key: str
    candidates: int


# The fixed top-ups automatic top-up buys: the smallest of each volume price, at that price
# (helpers/credits.py), in the buyer's currency.
TOP_UPS = [
    TopUp("topup_50", 10),
    TopUp("topup_200", 50),
    TopUp("topup_600", 200),
    TopUp("topup_1000", 500),
]

# What a candidate costs in a top-up of at least this many candidates, smallest first, in each
# currency, in its smallest unit as Paddle counts it (cents; yen and won themselves): volume prices, so larger top-ups buy candidates for less. Each
# currency has round prices of its own, not a conversion.
CANDIDATE_PRICES = {
    Currency.USD: [(10, 500), (50, 400), (200, 300), (500, 200)],
    Currency.EUR: [(10, 500), (50, 400), (200, 300), (500, 200)],
    Currency.GBP: [(10, 400), (50, 300), (200, 225), (500, 150)],
    Currency.CAD: [(10, 700), (50, 550), (200, 400), (500, 275)],
    Currency.AUD: [(10, 750), (50, 600), (200, 450), (500, 300)],
    Currency.ILS: [(10, 1800), (50, 1500), (200, 1100), (500, 750)],
    Currency.PLN: [(10, 1800), (50, 1500), (200, 1100), (500, 750)],
    Currency.JPY: [(10, 750), (50, 600), (200, 450), (500, 300)],
    Currency.KRW: [(10, 7000), (50, 5500), (200, 4000), (500, 2750)],
    Currency.TWD: [(10, 16000), (50, 13000), (200, 9500), (500, 6500)],
    Currency.HKD: [(10, 4000), (50, 3100), (200, 2300), (500, 1600)],
    Currency.CHF: [(10, 450), (50, 350), (200, 260), (500, 175)],
    Currency.THB: [(10, 17000), (50, 13500), (200, 10000), (500, 7000)],
    Currency.SGD: [(10, 650), (50, 530), (200, 400), (500, 265)],
    Currency.INR: [(10, 42000), (50, 34000), (200, 25000), (500, 17000)],
}

# A top-up of any number of candidates: from the smallest tier's candidates up to this many.
# Each candidate costs its tier's price (helpers/credits.py).
# Billing sells every top-up as one item priced in the transaction itself (quantity 1, which the
# buyer can't change), in one currency, with what it buys in the price's custom data: a fixed
# top-up's key under TOP_UP_FLAG, or the candidates under CUSTOM_TOP_UP_FLAG, recorded as
# CUSTOM_TOP_UP_KEY.
CUSTOM_TOP_UP_MAX = 1_000
TOP_UP_FLAG = "top_up"
CUSTOM_TOP_UP_FLAG = "candidates"
CUSTOM_TOP_UP_KEY = "candidates"

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
# Using credits waits this long at most for an automatic top-up's charge: Cloud Run slows the CPU
# once the answer is sent, so it can't run after it. A charge cut off is treated as one whose
# answer was lost (AUTO_TOP_UP_UNCREDITED_WAIT).
AUTO_TOP_UP_WAIT_SECONDS = 5
# Turning it on is a checkout for a $0 monthly subscription, which saves the card; Paddle tells
# us when it starts and when it ends (cancelled in Paddle, or after failed payments).
SUBSCRIPTION_CREATED = "subscription.created"
SUBSCRIPTION_CANCELED = "subscription.canceled"
SUBSCRIPTION_UPDATED = "subscription.updated"
# A subscription's status in Paddle once it has ended.
SUBSCRIPTION_ENDED_STATUS = "canceled"
# The change Paddle schedules when its customer cancels through Paddle's own email link or portal
# (for the end of the billing period): billing ends it at once instead.
SCHEDULED_CANCEL = "cancel"
# Marks the checkout that turns automatic top-up on.
AUTO_TOP_UP_FLAG = "auto_top_up"
# A running automatic top-up charges its buyer's card: only they change what it buys or when.
NOT_YOUR_AUTO_TOP_UP = (
    "Only the person whose card pays for it can change it. Turn it off, then turn it on with "
    "your own card."
)
# Saving it needs the buyer's tick on what it charges, when and how to turn it off: every save
# is a new agreement to its terms.
AGREEMENT_NEEDED = "Tick the box to agree to the automatic top-up's charges."
# Its terms as the company's action log keeps them with the buyer's agreement, in the buyer's
# language (prepza_common.i18n messages).
AGREED_TERMS = (
    "{price} plus tax when the balance falls under "
    "{threshold, plural, one {# credit} other {# credits}}"
)
PADDLE_API = {"sandbox": "https://sandbox-api.paddle.com", "production": "https://api.paddle.com"}
# The version of Paddle's API every call asks for (its `Paddle-Version` header), so a new default
# version in Paddle's dashboard can't change the answers billing reads.
PADDLE_API_VERSION = "1"
# Paddle's answers that refuse billing itself rather than the request: its API key is wrong,
# expired or lacks a permission, or billing is over Paddle's rate limit. Every call fails until
# fixed, so they count towards the "prepza Paddle failing" alert as an outage does.
PADDLE_REFUSES_BILLING = {401, 403, 429}
# How Paddle starts each environment's server-side API keys and client-side tokens: a key or
# token of the other environment stops billing from starting, so sandbox and live never mix.
PADDLE_KEY_PREFIXES = {"sandbox": "pdl_sdbx_", "production": "pdl_live_"}
PADDLE_TOKEN_PREFIXES = {"sandbox": "test_", "production": "live_"}
