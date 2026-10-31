from testee_common.i18n import error_codes as shared

# The machine-readable `code` every refusal of the public API carries beside its translated
# `detail` (clients branch on it, never on the text). Stable: a code is never changed or reused,
# only added. Companies' own (app/constants/error_codes.py there) come through as they are.
INVALID_API_KEY = "invalid_api_key"
API_KEY_EXPIRED = "api_key_expired"
IP_NOT_ALLOWED = "ip_not_allowed"
REQUEST_IN_PROGRESS = "request_in_progress"
IDEMPOTENCY_KEY_REUSED = "idempotency_key_reused"
VALIDATION_FAILED = "validation_failed"

# A refusal without a code of its own carries its status's.
BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    402: shared.INSUFFICIENT_CREDITS,
    403: "forbidden",
    404: shared.NOT_FOUND,
    405: "method_not_allowed",
    409: "conflict",
    413: shared.BODY_TOO_LARGE,
    422: VALIDATION_FAILED,
    429: shared.RATE_LIMITED,
    503: "unavailable",
}
