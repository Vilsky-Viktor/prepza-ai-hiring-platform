# What the public routes can answer besides their success, for the API reference: every
# refusal has the Error body (schemas/errors.py) and its machine-readable `code`.
from app.helpers.docs import refusal

RETRY_AFTER = {
    "Retry-After": {
        "description": "How many seconds to wait before trying again",
        "schema": {"type": "integer"},
    }
}
# Every public route can answer these.
COMMON = {
    401: refusal(
        "The API key is missing, invalid or expired, or its creator can no longer use it "
        "(`invalid_api_key`, `api_key_expired`, `key_creator_lost_access`)"
    ),
    403: refusal(
        "The API key doesn't have the permission the endpoint needs (`missing_permission`)"
    ),
    429: {
        **refusal("Your company's keys exceeded 60 requests per minute (`rate_limited`)"),
        "headers": RETRY_AFTER,
    },
    503: refusal(
        "prepza is down for maintenance (`maintenance`), or what the endpoint does is paused "
        "for a while (`paused`); try again later"
    ),
}
NOT_FOUND = {404: refusal("The interview or candidate doesn't exist in your company (`not_found`)")}
