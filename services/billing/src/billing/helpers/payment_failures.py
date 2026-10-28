from billing.constants.payment_failures import (
    CARD_METHOD,
    ERROR_CODE_FAILURES,
    VAGUE_ERROR_CODES,
    PaymentFailure,
)


def latest_failure(transaction: dict) -> PaymentFailure | None:
    """Why the transaction's latest payment attempt failed (Paddle lists the newest first); None
    while that attempt has no error code yet."""
    payments = transaction.get("payments") or []

    if not payments:
        return None

    latest = payments[0]
    code = latest.get("error_code")
    method = (latest.get("method_details") or {}).get("type")

    if code in VAGUE_ERROR_CODES and method and method != CARD_METHOD:
        return PaymentFailure.PAYMENT_METHOD_FAILED

    if code is None:
        return None

    return ERROR_CODE_FAILURES.get(code, PaymentFailure.OTHER)


def paid_by(transaction: dict, owner_type: str, owner_id: str, buyer_id: str) -> bool:
    """Whether the transaction is this buyer's checkout into this wallet, by the custom data
    billing set on it (a top-up's, or the automatic top-up's)."""
    custom = transaction.get("custom_data") or {}

    return (
        custom.get("owner_type") == owner_type
        and custom.get("owner_id") == owner_id
        and custom.get("buyer_id") == buyer_id
    )
