# Amounts are whole credits; a candidate takes CANDIDATE_CREDITS, whatever the top-up bought them for.
CANDIDATE_CREDITS = 500
# A new company gets its first 3 candidates.
WELCOME_COMPANY = 3 * CANDIDATE_CREDITS
# Below this, a balance is shown as running low, so a company sees it before it can't invite the
# next candidate.
LOW_BALANCE = CANDIDATE_CREDITS
# Both sides get it once the new company first tops up, any amount; a referrer is rewarded for at
# most REFERRALS_PER_YEAR.
REFERRAL_REWARD = 1000
REFERRALS_PER_YEAR = 25
REFERRAL_CODE_BYTES = 6

NOT_ENOUGH = "Not enough credits. Top up to continue."

# A superadmin's adjustment (its limits are in prepza_common.config.constants) removing credits the
# company has set aside for candidates, or doesn't have; or moving none.
ADJUSTMENT_BELOW_ZERO = "That would take the available balance below zero."
ADJUSTMENT_ZERO = "The amount can't be zero."


class Reason:
    """Why credits moved, as the history shows it."""

    WELCOME = "welcome"
    TOPUP = "topup"
    CANDIDATE = "candidate"
    # Paddle refunded a top-up, or the bank reversed it: the credits it bought go back.
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    # Paddle won a chargeback back: the credits return.
    CHARGEBACK_REVERSED = "chargeback_reversed"
    REFERRAL = "referral"
    # The top-up that paid a referral was refunded in full or charged back: both rewards go back.
    REFERRAL_REVERSED = "referral_reversed"
    # A superadmin added or removed credits, with a note saying why (a complaint, say).
    ADJUSTMENT = "adjustment"


# Every reason, for the database's check of entries.reason.
REASONS = tuple(value for name, value in vars(Reason).items() if not name.startswith("_"))

# Paddle's adjustments of a top-up.
ADJUSTMENTS = (Reason.REFUND, Reason.CHARGEBACK, Reason.CHARGEBACK_REVERSED)

# A candidate's hold and charge are keyed by this and the key companies gives the invite.
CANDIDATE_PREFIX = "candidate:"

# Names the welcome gift (helpers/gifts.py): a person's first company.
WELCOME_GIFT = "company"


class HoldStatus:
    OPEN = "open"
    CHARGED = "charged"
    RELEASED = "released"


HOLD_STATUSES = (HoldStatus.OPEN, HoldStatus.CHARGED, HoldStatus.RELEASED)
