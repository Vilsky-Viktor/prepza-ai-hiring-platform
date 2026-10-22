# The get_updates tool: what reached the bells of the user's companies since the last check, for
# AI apps over MCP and the in-app panel alike. It reads the notifications service's feed (an
# internal route), so it isn't an allow-list entry of a user-facing route: it's added to the
# registry by hand (services/registry.py) and carried out by services/updates.py.

GET_UPDATES = "get_updates"
GET_UPDATES_DEFINITION = {
    "type": "function",
    "function": {
        "name": GET_UPDATES,
        "description": (
            "What's new in the user's companies since the last check through this connection (the"
            " first time, and in prepza's own assistant, the last 7 days): each candidate who "
            "started or finished, with their grade and whether they passed; invites that weren't "
            "delivered; each candidate from an ATS who couldn't be invited; each question flagged"
            " or fixed; interviews ready or cancelled, automatic top-ups and the other "
            "notifications prepza's bell shows; and companies running low on credits. First a "
            "summary with counts, then the updates grouped by company and interview, newest "
            "first, each with a link to its page in prepza. Call it when the user asks what's new"
            " or how hiring is going, or starts a conversation about their candidates. It marks "
            "nothing as read in prepza."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "since": {
                    "type": "string",
                    "format": "date-time",
                    "maxLength": 40,
                    "description": (
                        "An ISO 8601 time: the updates since then instead of since the last "
                        "check (and it doesn't count as a check)."
                    ),
                },
                "company_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Only this company's updates.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
}
# The notifications service's route it reads.
UPDATES_PATH = "/internal/updates"

# The first check of a connection, and every check without one (the panel), covers this many
# days; the bell keeps nothing older than KEEP_DAYS, so a check older than that is forgotten.
FIRST_CHECK_DAYS = 7
KEEP_DAYS = 90
# A check of a connection covers up to this long before it's made (see services/updates.py).
SETTLE_SECONDS = 30
# The summary's count of the finished candidates who passed (not a kind of update).
PASSED = "passed"
# Each update comes from the service that holds it, one per candidate or question: candidates'
# steps from companies, ATS candidates not invited from ats, questions flagged or fixed from
# library (their internal routes). The bell's own notifications of those kinds, which it groups,
# are left out, so none is told twice; the bell gives the rest (none of which it groups).
CANDIDATE_UPDATES_PATH = "/internal/candidates/updates"
NOT_INVITED_PATH = "/internal/candidates/not-invited"
QUESTION_UPDATES_PATH = "/internal/questions/updates"
ATS_NOT_INVITED = "ats_not_invited"
FROM_SOURCES = frozenset(
    {
        "candidate_started",
        "candidate_finished",
        "invite_undelivered",
        ATS_NOT_INVITED,
        "question_flagged",
        "question_fixed",
    }
)
SOURCE_FIELDS = ("candidate_name", "email", "grade", "passed", "ats", "reason", "topic")
# What an update keeps of a bell notification's data (its title names its interview).
BELL_FIELDS = ("ats", "credits")
# A company running low on credits that no automatic top-up refills (billing's say, as for its
# reminder emails), on every check while it lasts, for those who may see its credits: its owners
# and admins, and API keys with credits:read.
CREDITS_LOW = "credits_low"
# The tool whose key permission (credits:read) lets an API key see them.
CREDITS_TOOL = "get_credits"
LOW_COMPANIES_PATH = "/internal/companies/low"
TOP_UP_PATH = "/top-up"

INVALID_SINCE = "since must be an ISO 8601 time, like 2026-10-01T09:00:00Z."
