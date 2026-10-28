# The `show` tool: the model's one way to put something under its answer, when it's part of the
# answer. Reads never show anything themselves. At most one list of rows and one link an answer.

SHOW = "show"

# Rows: the block's kind, and the ids each row needs (the model gives them).
ROW_KINDS = {
    "candidates": ("candidate_rows", ("interview_id", "candidate_id")),
    "interviews": ("interview", ("interview_id",)),
    "balances": ("credits", ("company_id",)),
}
# The page with every item of a list, under its rows: an interview's candidates, a company's
# interviews.
ALL_PAGES = {"candidate_rows": "interview_candidates", "interview": "company"}
# At most this many rows under an answer; a list of more links to the page with all of them.
MAX_ROWS = 10

# The app's pages a link may open, by name: their paths, filled only with ids (the model never
# writes a URL), and what names the page on its button (read with the user's token).
PAGES = {
    "interview": "/companies/{company_id}/interviews/{interview_id}",
    "interview_candidates": "/companies/{company_id}/interviews/{interview_id}/candidates",
    "candidate": "/companies/{company_id}/interviews/{interview_id}/candidates/{candidate_id}",
    "company": "/companies/{company_id}/interviews",
    "members": "/companies/{company_id}/members",
    "templates": "/companies/{company_id}/templates",
    "template": "/companies/{company_id}/templates/{template_id}",
    "integrations": "/companies/{company_id}/integrations",
    "ats": "/companies/{company_id}/integrations/{provider}",
    "slack": "/companies/{company_id}/integrations/slack",
    "api": "/companies/{company_id}/integrations/api",
    "referrals": "/companies/{company_id}/referrals",
    "top_up": "/top-up",
    "pricing": "/pricing",
    "settings": "/settings",
    "faq": "/faq",
    "contact": "/contact",
    "news": "/news",
    "guide": "/guides/{slug}",
}
# Pages named by what they're about: the service and read giving the name, and its field.
PAGE_NAMES = {
    "interview": ("companies", "/interviews/{interview_id}", "title"),
    "interview_candidates": ("companies", "/interviews/{interview_id}", "title"),
    "company": ("companies", "/companies/{company_id}", "name"),
    "guide": ("site", "/help/guides/{slug}", "title"),
}
# Reads of a setting, and the page it's changed on: an answer about one links there when the
# model gave no link (show.implied_link).
SETTING_PAGES = {
    "get_auto_top_up": "top_up",
    "get_slack": "slack",
    "list_ats_connections": "integrations",
    "get_api_settings": "api",
}
# The ids a link may be filled with.
LINK_IDS = ("company_id", "interview_id", "candidate_id", "template_id", "provider", "slug")

SHOW_DEFINITION = {
    "type": "function",
    "function": {
        "name": SHOW,
        "description": (
            "Put something under your answer, only when it is part of the answer. "
            "kind 'candidates', 'interviews' or 'balances': rows, only when the user asked to "
            "list or show them, and only the rows that answer (e.g. the best candidate's row, "
            "not everyone's), as `rows` of ids. kind 'link': one link to the single most "
            "relevant, most specific page (`page` and its ids), e.g. the interview's page for a "
            "question about a position, the candidate's report for a candidate. At most one "
            "rows and one link per answer; none for small talk. Rows are at most 10: a list of "
            "candidates or interviews gets a link to the page with all of them by itself, so add "
            "no link of your own to that page."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": [*ROW_KINDS, "link"]},
                "rows": {
                    "type": "array",
                    "maxItems": MAX_ROWS,
                    "items": {
                        "type": "object",
                        "properties": {
                            "interview_id": {"type": "string"},
                            "candidate_id": {"type": "string"},
                            "company_id": {"type": "string"},
                        },
                    },
                },
                "page": {"type": "string", "enum": list(PAGES)},
                "company_id": {"type": "string"},
                "interview_id": {"type": "string"},
                "candidate_id": {"type": "string"},
                "template_id": {"type": "string"},
                "provider": {"type": "string"},
                "slug": {"type": "string"},
            },
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
}

# What the model reads back (it isn't the user's text).
SHOWN = "Shown under your answer."
ONE_EACH = "Only one list and one link per answer: this one wasn't shown."
NOTHING_TO_SHOW = "Nothing to show: those ids aren't ones the user can see, or the page is unknown."
