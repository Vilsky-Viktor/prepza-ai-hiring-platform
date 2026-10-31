# What the public routes can answer besides their success, for the API reference: every
# refusal has the Error body (schemas/errors.py) and its machine-readable `code`.
from api.helpers.docs import refusal

RETRY_AFTER = {
    "Retry-After": {
        "description": "How many seconds to wait before trying again",
        "schema": {"type": "integer"},
    }
}
LINK_NEXT = {
    "Link": {
        "description": (
            'The next page\'s address, as `<url>; rel="next"`, when this page is full; absent '
            "on the last page"
        ),
        "schema": {"type": "string"},
    }
}
# A list's success: the page, and the next one's address.
LISTED = {"description": "Successful Response", "headers": LINK_NEXT}
DEPRECATION_HEADERS = {
    "Deprecation": {
        "description": "When this endpoint was deprecated (RFC 9745), as `@<unix time>`",
        "schema": {"type": "string"},
    },
    "Sunset": {
        "description": "When this endpoint stops working (RFC 8594), as an HTTP date",
        "schema": {"type": "string"},
    },
    "Link": {
        "description": 'The changelog that says what to use instead (`rel="deprecation"`)',
        "schema": {"type": "string"},
    },
}

# Every public route can answer these.
COMMON = {
    401: refusal(
        "The API key is missing, invalid or expired (`invalid_api_key`, `api_key_expired`)"
    ),
    403: refusal(
        "The API key doesn't have the permission the endpoint needs (`missing_permission`), or "
        "doesn't allow the address the request came from (`ip_not_allowed`)"
    ),
    429: {
        **refusal("Your company's keys exceeded 60 requests per minute (`rate_limited`)"),
        "headers": RETRY_AFTER,
    },
    503: refusal(
        "testee is down for maintenance (`maintenance`), or what the endpoint does is paused "
        "for a while (`paused`); try again later"
    ),
}
NOT_FOUND = {404: refusal("The interview or candidate doesn't exist in your company (`not_found`)")}
