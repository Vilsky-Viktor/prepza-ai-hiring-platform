# More reads (see tools.py for the entries' keys): an interview's questions and their reports,
# the company's action log, its credit history and reserved credits, the user's email settings,
# templates to copy, an ATS job's stages and text, prepza's news and the user's own practice.

from prepza_common.config.constants import MAX_GOAL_LENGTH

# A credited candidate, in the history and the reserved list.
CREDIT_CANDIDATE_FIELDS = ["invite_id", "interview_id", "email", "name", "interview_title"]

DETAIL_TOOLS = {
    "list_topic_questions": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/topics/{topic_id}/questions",
        "params": ["interview_id", "topic_id"],
        # Fields are kept at every level: "answer" and "correct" are each option's.
        "fields": [
            "id",
            "text",
            "options",
            "answer",
            "correct",
            "multi",
            "likes",
            "dislikes",
            "reports",
        ],
        "max_items": 30,
    },
    "list_question_reports": {
        "service": "companies",
        "method": "GET",
        "path": "/interviews/{interview_id}/questions/{question_id}/reports",
        "params": ["interview_id", "question_id", "offset", "limit"],
        "fields": ["id", "reason", "comment", "created_at"],
    },
    # The owner's only: who did what in the company, filtered by member, group and days.
    "list_company_actions": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/actions",
        "params": ["company_id", "member_id", "group", "from", "to", "offset", "limit"],
        "fields": [
            "action",
            "group",
            "user_email",
            "target_kind",
            "target",
            "removed",
            "via",
            "created_at",
        ],
    },
    # Never an invoice: its temporary link is the payment provider's (the billing page has it).
    "list_credit_history": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/billing/history",
        "params": ["company_id", "offset", "limit"],
        "fields": [
            "amount",
            "reason",
            "created_at",
            "total",
            "currency",
            "automatic",
            "candidate",
            "candidate_deleted",
            *CREDIT_CANDIDATE_FIELDS,
        ],
    },
    "list_reserved_credits": {
        "service": "companies",
        "method": "GET",
        "path": "/companies/{company_id}/billing/reserved",
        "params": ["company_id", "offset", "limit"],
        "fields": CREDIT_CANDIDATE_FIELDS,
    },
    "get_email_preferences": {
        "service": "accounts",
        "method": "GET",
        "path": "/me/email-preferences",
        "params": [],
    },
    "list_copyable_templates": {
        "service": "library",
        "method": "GET",
        "path": "/templates/copyable",
        "params": ["q", "level", "language", "offset", "limit"],
        "fields": ["id", "title", "level", "language", "topic_count"],
    },
    "list_ats_stages": {
        "service": "ats",
        "method": "GET",
        "path": "/{provider}/jobs/{job_id}/stages",
        "params": ["provider", "job_id", "company_id"],
        "fields": ["id", "name"],
    },
    # To make an interview from the job (its description, the same limit as a pasted one).
    "get_ats_job_text": {
        "service": "ats",
        "method": "GET",
        "path": "/{provider}/jobs/{job_id}/text",
        "params": ["provider", "job_id", "company_id"],
        "fields": ["text"],
        "max_length": MAX_GOAL_LENGTH,
    },
    "list_news": {
        "service": "library",
        "method": "GET",
        "path": "/news",
        "params": ["offset", "limit"],
        "fields": ["id", "title", "text", "published_on"],
        "max_items": 10,
    },
    "list_practice_rounds": {
        "service": "rounds",
        "method": "GET",
        "path": "/practice/{template_id}/rounds",
        "params": ["template_id"],
        "fields": ["round_id", "started_at", "finished", "progress", "grade"],
    },
    "get_practice_progress": {
        "service": "rounds",
        "method": "GET",
        "path": "/practice/{template_id}/progress",
        "params": ["template_id"],
        "fields": ["topic_id", "answered", "total"],
    },
}
