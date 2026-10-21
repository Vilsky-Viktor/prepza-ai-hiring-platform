# Automatic top-up's declined charges, within card networks' rules for retries (Visa: at most 15
# in 30 days, and none after a decline it marks "never retry"; Mastercard's advice codes alike).
from datetime import timedelta

# Paddle's `payments[].error_code` for a card that won't pay however often it's tried: stolen,
# lost or blocked, closed, expired, refused for good, or one that needs its holder (a bank check,
# details to correct). Automatic top-up pauses at once. Any other code, an unknown one or none,
# is a decline that may pass later (no funds, the bank unreachable).
HARD_DECLINE_CODES = frozenset(
    {
        "declined_not_retryable",
        "blocked_card",
        "fraud",
        "expired_card",
        "invalid_payment_details",
        "authentication_failed",
        "preferred_network_not_supported",
        "prepaid_card_not_supported",
        "transaction_not_permitted",
    }
)

# After the first, second and third decline in a row, the next try waits this long; a fourth
# decline pauses automatic top-up until the card is updated. Four tries in 11 days.
AUTO_TOP_UP_RETRY_WAITS = (timedelta(days=1), timedelta(days=3), timedelta(days=7))

# Reading why the card declined waits this long at most: the request that used the credits is
# held while it does (AUTO_TOP_UP_WAIT_SECONDS), and the decline already counts without it.
DECLINE_READ_TIMEOUT_SECONDS = 2

# The origin Paddle gives the transaction that saves a subscription's new card.
PAYMENT_METHOD_CHANGE_ORIGIN = "subscription_payment_method_change"
