# The assistant's tools: user-facing GET routes of the other services, called with the user's own
# token, so roles and every other rule apply there unchanged. Each entry names its service and
# route (the path as that service sees it, in its snapshot in app/openapi/), and:
# - params: the route's parameters the model may set (every required one among them);
# - fields: the keys the model reads, at every level of the data (all when left out);
# - max_items: the longest list it reads (DEFAULT_MAX_ITEMS when left out); a `limit` the model
#   sets is capped at it;
# - max_length: the longest string it reads (MAX_STRING_LENGTH when left out);
# - description: what the model is told the tool does (the route's docstring when left out).
# A new tool is a new entry here; scripts/assistant-openapi.sh refreshes the snapshots. Reads
# show the user nothing themselves: the model reads them and answers, and shows rows or a link
# only through the `show` tool (constants/show.py).


from app.constants.actions import ACTIONS
from app.constants.company_tools import COMPANY_TOOLS
from app.constants.detail_tools import DETAIL_TOOLS

TOOLS = {
    **COMPANY_TOOLS,
    **DETAIL_TOOLS,
    **ACTIONS,
    "get_price_catalog": {
        "service": "billing",
        "method": "GET",
        "path": "/catalog",
        "params": [],
        # Not Paddle's settings.
        "fields": [
            "currency",
            "candidate_credits",
            "candidate_prices",
            "candidate_cents_min",
            "candidate_cents_max",
            "welcome_company",
            "free_candidates",
            "referral_company",
            "from_cents",
            "cents",
            "products",
            "key",
            "price_cents",
            "credits",
            "candidates",
            "candidate_cents",
        ],
    },
    "list_ats_connections": {
        "service": "ats",
        "method": "GET",
        "path": "/connections",
        "params": ["company_id"],
    },
    "list_ats_links": {
        "service": "ats",
        "method": "GET",
        "path": "/links",
        "params": ["company_id"],
    },
    "list_ats_jobs": {
        "service": "ats",
        "method": "GET",
        "path": "/{provider}/jobs",
        "params": ["provider", "company_id"],
    },
    "get_slack": {
        "service": "notifications",
        "method": "GET",
        "path": "/slack",
        "params": ["company_id"],
        "fields": ["connected", "status", "team", "channel", "kinds", "all_kinds"],
    },
    "get_api_settings": {
        "service": "api",
        "method": "GET",
        "path": "/manage",
        "params": ["company_id"],
        # Never a web hook's URL, which can carry a secret.
        "fields": [
            "keys",
            "webhooks",
            "id",
            "name",
            "shown",
            "created_at",
            "expires_at",
            "expired",
            "last_used_at",
            "failing",
        ],
    },
    "list_notifications": {
        "service": "notifications",
        "method": "GET",
        "path": "/me",
        "params": [],
        "fields": [
            "items",
            "unread",
            "id",
            "kind",
            "data",
            "created_at",
            "title",
            "topic",
            "count",
            "credits",
            "email",
            "ats",
        ],
    },
    "get_me": {
        "service": "library",
        "method": "GET",
        "path": "/me",
        "params": [],
        "fields": ["email", "email_verified", "name", "language"],
    },
    "search_templates": {
        "service": "library",
        "method": "GET",
        "path": "/templates",
        "params": ["q", "level", "language", "offset", "limit"],
        "fields": ["id", "title", "level", "language", "topic_count"],
    },
    "list_template_filters": {
        "service": "library",
        "method": "GET",
        "path": "/templates/filters",
        "params": [],
    },
    "get_template": {
        "service": "library",
        "method": "GET",
        "path": "/templates/{key}",
        "params": ["key"],
        "fields": ["id", "title", "level", "language", "topic_count", "topics", "subtopics"],
    },
    "get_faq": {
        "service": "rounds",
        "method": "GET",
        "path": "/help/faq",
        "params": [],
        "fields": ["question", "answer"],
        "max_items": 100,
        "max_length": 2_000,
    },
    "get_page_guide": {
        "service": "rounds",
        "method": "GET",
        "path": "/help/pages/{key}",
        "params": ["key"],
        "fields": ["key", "title", "text", "actions", "tips", "article", "slug"],
        "description": (
            "A page's guide, in the user's language: what the page is for, what you can do there "
            "and tips. Pass the key of the page the user is on (named in the context), or of "
            'another page they ask about. Use it for "how do I use this page", "what can I do '
            'here" and "what is this page" questions.'
        ),
    },
    "list_guides": {
        "service": "rounds",
        "method": "GET",
        "path": "/help/guides",
        "params": [],
        "fields": ["slug", "title", "description"],
        "description": (
            "prepza's guide articles, by title and summary, in the user's language: in-depth "
            "hiring advice and how-tos (how to hire and screen, what to test, the law on AI in "
            "hiring, connecting an ATS, AI agents and the API, setting up a test). Use it for "
            'advice, best-practice and "how should I" questions, then read the fitting one '
            "with get_guide."
        ),
    },
    "get_guide": {
        "service": "rounds",
        "method": "GET",
        "path": "/help/guides/{slug}",
        "params": ["slug"],
        "fields": ["slug", "title", "updated", "body"],
        # A whole article.
        "max_length": 40_000,
        "description": (
            "One guide article, by its slug from list_guides, in the user's language: answer "
            "from it, and offer it with show (page 'guide' and its slug)."
        ),
    },
    "get_platform_guide": {
        "service": "rounds",
        "method": "GET",
        "path": "/help/guide",
        "params": [],
        # The whole guide, which is long.
        "max_length": 100_000,
        "description": (
            "Everything prepza's help knows, in the user's language: what prepza can do and how "
            "to use each feature, the FAQ, today's prices and credits, payments and refunds, "
            "the terms of use and the privacy policy. Use it for how-to, pricing, policy and "
            '"what can prepza do" questions, before saying you don\'t know.'
        ),
    },
}
