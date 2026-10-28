import re

# Each tool call waits this long for its service (an ATS's job list is a live call to the ATS).
TOOL_TIMEOUT_SECONDS = 20
# Tool calls one step of a turn runs at the same time.
MAX_PARALLEL_TOOL_CALLS = 4
# What a tool's data may hold for the model: lists of at most a tool's max_items (or
# DEFAULT_MAX_ITEMS), strings of at most MAX_STRING_LENGTH characters.
DEFAULT_MAX_ITEMS = 20
MAX_STRING_LENGTH = 300
# The methods of the routes that change something: each waits for the user's confirmation.
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
# Routes the assistant never calls: other services' and prepza's own team's.
FORBIDDEN_PATH_PREFIXES = ("/internal", "/superadmin")
# A referral code as billing makes them (URL-safe): only one that reads right is passed on, in
# the cookie companies reads.
REFERRAL_CODE = re.compile(r"[A-Za-z0-9_-]{1,64}")
# Where each tool's service is: the settings attribute holding its base URL.
SERVICE_URLS = {
    "companies": "companies_url",
    "billing": "billing_url",
    "library": "library_url",
    "accounts": "accounts_url",
    "notifications": "notifications_url",
    "ats": "ats_url",
    "api": "api_url",
    "rounds": "rounds_url",
}
# What the model reads when a tool's service didn't answer.
SERVICE_UNAVAILABLE = "The service didn't answer. Try again later."
# What the model reads for a call it can correct, with what to do next. INVALID_ARGUMENTS is
# followed by ": " and what's wrong, when that's known.
INVALID_ARGUMENTS = "The arguments don't match the tool's schema; correct them and call it again"
UNKNOWN_TOOL = "There is no such tool: use one of the tools listed for you, by its exact name."
# What the model reads under a list cut short: how to see the rest. A list tool's query
# parameters narrow it, but these, which page or order it or name its scope.
NOT_FILTERS = ("limit", "offset", "sort", "company_id")
MORE_ITEMS = "More exist than shown."
NARROW_WITH = "Narrow the call with {filters}, or ask the user how to narrow it."
ASK_TO_NARROW = "Say so, and ask the user how to narrow it."
NEXT_PAGE = "For the next ones, call again with offset {offset}."
# A link's secret code in a tool's data, and the full link the model gets in its place, as the
# app's pages copy it: the candidate's invite and the interview's shareable link.
TOKEN_LINKS = {
    "invite_token": ("invite_url", "/invite/{}"),
    "link_token": ("link_url", "/apply/{}"),
}
