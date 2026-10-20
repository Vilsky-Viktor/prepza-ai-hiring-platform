# The assistant split by domain (ASSISTANT_MODE=subagents): the main agent keeps the conversation
# and answers common reads itself; each domain's agent gets only its own tools, and the main
# agent hands it a part of the request through one delegate tool per domain. Every registry tool
# is the main agent's or one domain's (tests/unit/test_subagents.py checks it).

from enum import StrEnum


class AssistantMode(StrEnum):
    # One agent with every tool.
    SINGLE = "single"
    # The main agent with delegates to the domains' agents.
    SUBAGENTS = "subagents"


# What the main agent reads itself: finding companies, interviews and candidates, results and
# balances, the help and the panel's updates.
MAIN_TOOLS = (
    "list_companies",
    "get_company",
    "list_company_balances",
    "get_credits",
    "list_interviews",
    "get_interview",
    "get_interview_report",
    "list_candidates",
    "search_candidates",
    "get_scorecard",
    "get_page_guide",
    "list_guides",
    "get_guide",
    "get_platform_guide",
    "get_faq",
    "get_me",
    "get_updates",
)

# Each domain: its own tools, and the main agent's finders it may use too (`shared`).
DOMAINS = {
    "candidates": {
        "tools": (
            "invite_candidate",
            "invite_candidates",
            "revoke_candidate",
            "rename_candidate",
            "set_extra_time",
            "mark_hired",
        ),
        "shared": ("list_interviews", "list_candidates", "search_candidates", "get_scorecard"),
    },
    "interviews": {
        "tools": (
            "create_interview",
            "create_interview_from_template",
            "delete_interview",
            "rename_interview",
            "set_pass_mark",
            "set_question_seconds",
            "set_interview_link",
            "set_topic_limit",
            "regenerate_question",
            "mark_question_wrong",
            "review_generation",
            "retry_generation",
            "cancel_generation",
            "get_generation",
            "list_topic_questions",
            "list_question_reports",
            "search_templates",
            "get_template",
            "list_copyable_templates",
        ),
        # An interview made from an ATS job's text reads it itself.
        "shared": (
            "list_interviews",
            "get_interview",
            "list_ats_connections",
            "list_ats_jobs",
            "get_ats_job_text",
        ),
    },
    "company": {
        "tools": (
            "create_company",
            "rename_company",
            "delete_company",
            "set_company_website",
            "remove_company_logo",
            "invite_member",
            "change_member_role",
            "remove_member",
            "list_members",
            "get_referral",
            "list_company_actions",
            "get_pause",
        ),
        "shared": ("list_companies", "get_company"),
    },
    "billing": {
        "tools": (
            "get_auto_top_up",
            "turn_off_auto_top_up",
            "list_credit_history",
            "list_reserved_credits",
            "get_price_catalog",
        ),
        "shared": ("get_credits", "list_company_balances"),
    },
    "integrations": {
        "tools": (
            "list_ats_connections",
            "list_ats_links",
            "list_ats_jobs",
            "list_ats_stages",
            "get_ats_job_text",
            "link_ats_job",
            "unlink_ats_job",
            "retry_ats_candidates",
            "disconnect_ats",
            "get_slack",
            "set_slack_kinds",
            "disconnect_slack",
            "get_api_settings",
            "create_webhook",
            "remove_webhook",
            "remove_api_key",
        ),
        "shared": ("list_interviews",),
    },
    "account": {
        "tools": (
            "update_language",
            "update_email_preferences",
            "get_email_preferences",
            "delete_account",
            "list_notifications",
            "mark_notifications_seen",
            "list_news",
            "start_practice",
            "list_practice_rounds",
            "get_practice_progress",
            "list_template_filters",
        ),
        "shared": (),
    },
}

# The delegate tools' names: the prefix and the domain.
DELEGATE_PREFIX = "delegate_"
# What each delegate does, for the main agent (the tool's description).
DELEGATE_DESCRIPTIONS = {
    "candidates": (
        "Hand a candidate task to the candidates' agent: invite one or many candidates to an "
        "interview, revoke an invite, correct a candidate's name, give extra time, mark who was "
        "hired. It prepares the confirmation cards."
    ),
    "interviews": (
        "Hand an interview task to the interviews' agent: create an interview (from a job "
        "description, an ATS job's text or a template), rename or delete one, its settings (pass mark, seconds a "
        "question, its link, a topic's question count), its questions (read, regenerate, mark "
        "wrong, candidates' reports) and its generation (status, review, retry, cancel). It "
        "prepares the confirmation cards."
    ),
    "company": (
        "Hand a company or team task to the company's agent: create, rename or delete a "
        "company, its website and logo, the team (list, invite, change a role, remove), "
        "referrals, the company's activity log and a pause. It prepares the confirmation cards."
    ),
    "billing": (
        "Hand a billing question or task to the billing agent: auto top-up (read, turn off), "
        "the credit history, reserved credits and today's prices. Buying credits and turning "
        "auto top-up on happen on the top-up page, which it links."
    ),
    "integrations": (
        "Hand an integrations task to the integrations agent: ATS connections, jobs, their "
        "text and stages, linking a job to an interview, Slack, the API's keys and web hooks. "
        "Connecting an ATS or Slack and creating an API key happen on the integrations pages, "
        "which it links. An interview made from an ATS job is the interviews' agent's task."
    ),
    "account": (
        "Hand an account task to the account agent: the user's language and email "
        "preferences, deleting their account, notifications and news, practice rounds of a "
        "template."
    ),
}
DELEGATE_PARAMETERS = {
    "type": "object",
    "properties": {
        "task": {
            "type": "string",
            "description": (
                "The part of the user's request this agent does, in a sentence, with the "
                "values the user gave (emails, names, numbers) as they wrote them."
            ),
        },
        "company_id": {
            "type": ["string", "null"],
            "description": "The company's id, from the context or your tools' data; null if none.",
        },
        "interview_id": {
            "type": ["string", "null"],
            "description": "The interview's id, from your tools' data or the page; null if none.",
        },
    },
    "required": ["task", "company_id", "interview_id"],
    "additionalProperties": False,
}
# The ids a delegate call passes on in its brief.
BRIEF_IDS = ("company_id", "interview_id")
# What a domain's agent may call, at most: its tools, the shared finders and `show`.
MAX_DOMAIN_TOOLS = 25
