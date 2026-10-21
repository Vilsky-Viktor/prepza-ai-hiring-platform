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
    "notifications": "notifications_url",
    "ats": "ats_url",
    "api": "api_url",
    "rounds": "rounds_url",
}
# What the model reads when a tool's service didn't answer.
SERVICE_UNAVAILABLE = "The service didn't answer. Try again later."
INVALID_ARGUMENTS = "Invalid arguments"
UNKNOWN_TOOL = "There is no such tool."
# A link's secret code in a tool's data, and the full link the model gets in its place, as the
# app's pages copy it: the candidate's invite and the interview's shareable link.
TOKEN_LINKS = {
    "invite_token": ("invite_url", "/invite/{}"),
    "link_token": ("link_url", "/apply/{}"),
}
