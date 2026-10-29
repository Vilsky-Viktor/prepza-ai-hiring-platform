# The assistant's tools on companies' routes; see tools.py.

CANDIDATE_FIELDS = [
    "id",
    # From the candidate's sign-in, or as the company entered it; null when not known.
    "name",
    "email",
    "status",
    "grade",
    "passed",
    "progress",
    "tab_leaves",
    "copies",
    "fast_answers",
    "created_at",
]
INTERVIEW_FIELDS = [
    "id",
    "title",
    "status",
    "candidate_count",
    "pass_mark",
    "hired",
    "generation_failed",
    "question_seconds",
    "created_at",
]

COMPANY_TOOLS = {
    "list_companies": {
        "service": "companies",
        "method": "GET",
        "path": "/companies",
        "params": ["offset", "limit"],
        "fields": [
            "id",
            "name",
            "role",
            "interview_count",
            "website_domain",
            "verified_domain",
            "verification_status",
        ],
    },
    "get_company": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}",
        "params": ["company_id"],
        "fields": [
            "id",
            "name",
            "role",
            "can_edit",
            "can_manage_members",
            "interview_count",
            "website_domain",
            "verified_domain",
            "verification_status",
            "decline_reason",
            "allowed_domains",
            "allow_localhost",
            "created_at",
        ],
    },
    "list_company_balances": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/credits",
        "params": ["offset", "limit"],
        "fields": ["id", "name", "available", "low"],
    },
    "get_credits": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/credits",
        "params": ["company_id"],
    },
    "get_referral": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/referral",
        "params": ["company_id"],
    },
    "get_auto_top_up": {
        "service": "billing",
        "method": "GET",
        "path": "/companies/{company_id}/auto-top-up",
        "params": ["company_id"],
        # Each pack's price in `currency`, the company's, which every charge is in.
        "fields": ["offered", "on", "waiting", "product", "threshold", "currency", "prices"],
    },
    "list_members": {
        "service": "companies",
        "method": "GET",
        "path": "/members",
        "params": ["company_id", "offset", "limit"],
        # Never an admin invite's token.
        "fields": ["id", "email", "role", "joined", "created_at"],
    },
    "list_interviews": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews",
        "params": ["company_id", "offset", "limit"],
        "fields": INTERVIEW_FIELDS,
    },
    "get_interview": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}",
        "params": ["interview_id"],
        "fields": [
            *INTERVIEW_FIELDS,
            "can_edit",
            "topics",
            "subtopics",
            "question_count",
            "question_limit",
            # The shareable link, while it's on.
            "link_url",
        ],
    },
    "get_generation": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/generation",
        "params": ["interview_id"],
        "fields": [
            "status",
            "error",
            "language",
            "topics",
            "main_topic",
            "subtopics",
            "progress",
            "done",
            "total",
            "topics_ready",
        ],
    },
    "get_interview_report": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/report",
        "params": ["interview_id"],
        "fields": ["title", "pass_mark", "candidates", *CANDIDATE_FIELDS],
    },
    "list_candidates": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/candidates",
        "params": ["interview_id", "q", "status", "sort", "offset", "limit"],
        "fields": CANDIDATE_FIELDS,
    },
    "search_candidates": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/candidates",
        "params": ["company_id", "q", "offset", "limit"],
        "fields": [*CANDIDATE_FIELDS, "interview_id", "interview_title"],
    },
    "get_scorecard": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/candidates/{invite_id}",
        "params": ["interview_id", "invite_id"],
        "description": (
            "One candidate's results by interview_id and invite_id: their grade, whether they "
            "passed, each topic's score with its integrity signals (page leaves, copies, fast "
            "answers), and, once they finished, answer_patterns.signals: patterns in their "
            "answers and times (timing: times that didn't follow the questions' length and "
            "difficulty; person_fit: hard questions right while easy ones were wrong, with the "
            "counts). Signals can have innocent causes: they are reasons to ask, never a verdict."
        ),
        # Totals per topic; never the questions, the answers or their keys.
        "fields": [
            "id",
            "name",
            "email",
            "status",
            "title",
            "grade",
            "passed",
            "pass_mark",
            "sessions",
            "topic_title",
            "final_score",
            "tab_leaves",
            "copies",
            "fast_answers",
            # Patterns in the answers and times: the signals that fired, with their counts; not
            # the follow-up questions, which hold the questions and their keys.
            "answer_patterns",
            "signals",
            "kind",
            "hard",
            "hard_right",
            "easy",
            "easy_wrong",
            # Extra seconds per question, for a candidate who asked for more time.
            "extra_time",
            # Until the candidate finishes, for owners and admins: to send it themselves.
            "invite_url",
        ],
    },
    "get_pause": {
        "service": "companies",
        "method": "GET",
        "path": "/pause",
        "params": [],
    },
}
