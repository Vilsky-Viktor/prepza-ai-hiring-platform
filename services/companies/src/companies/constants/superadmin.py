import re
from enum import StrEnum

# The admin zone's companies tab lists at most this many: a search narrows it.
COMPANIES_SHOWN = 50

# The admin zone's support tab: a search finds at most this many results, in a query this long.
SUPPORT_RESULTS = 20
MAX_SUPPORT_QUERY = 300
# A link to (or path of) a company's page on testee's site, its interview's or its candidate's,
# on any host and under any language prefix.
COMPANY_PATH = re.compile(
    r"/companies/([0-9a-f-]{36})(?:/interviews/([0-9a-f-]{36})(?:/candidates/([0-9a-f-]{36}))?)?",
    re.IGNORECASE,
)
# A Paddle transaction, as a top-up's receipt shows it.
TRANSACTION_ID = re.compile(r"txn_[0-9a-z]+", re.IGNORECASE)
# What could be a testee account's id (Firebase's, or a guest candidate's), so nothing else is
# sent to library as one.
ACCOUNT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
# A candidate's credits, by the status of billing's hold for them.
CREDIT_STATES = {"open": "held", "charged": "charged", "released": "released"}


class SupportKind(StrEnum):
    """What a support search result is."""

    COMPANY = "company"
    INTERVIEW = "interview"
    CANDIDATE = "candidate"
    # A testee account: its id is the account's, its title the account's address.
    USER = "user"


class QueryKind(StrEnum):
    """What a support search's query is, as the logs say it (never the query itself: it may be
    an email address)."""

    LINK = "link"
    ID = "id"
    TRANSACTION = "transaction"
    EMAIL = "email"
    NAME = "name"
