from enum import StrEnum


class PaymentFailure(StrEnum):
    """Why a checkout's payment failed, as the buyer can act on it; the site says what to do for
    each."""

    CARD_DECLINED = "card_declined"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    EXPIRED_CARD = "expired_card"
    INVALID_DETAILS = "invalid_details"
    AUTHENTICATION_FAILED = "authentication_failed"
    CARD_NOT_SUPPORTED = "card_not_supported"
    PAYMENT_METHOD_FAILED = "payment_method_failed"
    TRY_LATER = "try_later"
    OTHER = "other"


# Paddle's `payments[].error_code` (developer.paddle.com, the transaction entity), by what the
# buyer can do about it. A code not listed here, a new one included, is OTHER.
ERROR_CODE_FAILURES = {
    "declined": PaymentFailure.CARD_DECLINED,
    "declined_not_retryable": PaymentFailure.CARD_DECLINED,
    "blocked_card": PaymentFailure.CARD_DECLINED,
    "fraud": PaymentFailure.CARD_DECLINED,
    "not_enough_balance": PaymentFailure.INSUFFICIENT_FUNDS,
    "expired_card": PaymentFailure.EXPIRED_CARD,
    "invalid_payment_details": PaymentFailure.INVALID_DETAILS,
    "authentication_failed": PaymentFailure.AUTHENTICATION_FAILED,
    "preferred_network_not_supported": PaymentFailure.CARD_NOT_SUPPORTED,
    "prepaid_card_not_supported": PaymentFailure.CARD_NOT_SUPPORTED,
    "transaction_not_permitted": PaymentFailure.CARD_NOT_SUPPORTED,
    "invalid_amount": PaymentFailure.CARD_NOT_SUPPORTED,
    "issuer_unavailable": PaymentFailure.TRY_LATER,
    "psp_error": PaymentFailure.TRY_LATER,
    "system_error": PaymentFailure.TRY_LATER,
}

# Codes that say nothing about why: for a payment method other than a card (PayPal, Apple Pay,
# Google Pay and so on), the failure is that method's.
VAGUE_ERROR_CODES = {None, "declined", "unknown"}
CARD_METHOD = "card"

# Paddle.js reports the failure as it happens; the attempt's code may reach Paddle's API a moment
# later. So the transaction is read up to this many times, this far apart, each read bounded, so
# the buyer isn't kept waiting long (about 5 s at most); Paddle not answering is OTHER. During a
# processor incident Paddle recorded the code after more than a second, so two reads a second apart
# showed the generic advice instead of "try later".
FAILURE_READS = 4
FAILURE_READ_WAIT_SECONDS = 1.5
FAILURE_READ_TIMEOUT_SECONDS = 4
# A Paddle transaction id, checked before it goes into Paddle's address.
TRANSACTION_ID_PATTERN = r"^txn_[a-z0-9]{26}$"
