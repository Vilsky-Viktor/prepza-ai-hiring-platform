from enum import StrEnum

# Each turn is offered the core tools and the groups a routing call picks for its message (at
# most MAX_GROUPS), not all of them: fewer tools a turn read fewer tokens (ai.md, Tools).
CORE_TOOLS = frozenset(
    {
        "list_companies",
        "get_company",
        "list_interviews",
        "get_interview",
        "list_candidates",
        "search_candidates",
        "get_scorecard",
        "get_page_guide",
        "get_guide",
        "list_guides",
        "get_platform_guide",
        "get_updates",
        "get_me",
    }
)
MAX_GROUPS = 2
# The conversation's last messages the routing call reads with the new one: a short reply
# ("the second one") needs what it answers.
ROUTING_MESSAGES = 4
ROUTING_MAX_TOKENS = 50
# The routing call holds up the turn: a slow or failed one offers every tool instead.
ROUTING_TIMEOUT_SECONDS = 5
ROUTING_RETRIES = 0


class ToolGroup(StrEnum):
    CANDIDATES = "candidates"
    INTERVIEW_SETUP = "interview_setup"
    TEMPLATES_PRACTICE = "templates_practice"
    TEAM_COMPANY = "team_company"
    BILLING = "billing"
    INTEGRATIONS = "integrations"
    ACCOUNT = "account"


# Every tool outside the core is in one group (tests/unit/test_tool_routing.py checks it).
TOOL_GROUPS = {
    ToolGroup.CANDIDATES: frozenset(
        {
            "invite_candidate",
            "invite_candidates",
            "revoke_candidate",
            "rename_candidate",
            "set_extra_time",
            "mark_hired",
            "get_interview_report",
            "list_interview_notes",
            "add_interview_note",
            "pin_interview_note",
        }
    ),
    ToolGroup.INTERVIEW_SETUP: frozenset(
        {
            "create_interview",
            "create_interview_from_template",
            "rename_interview",
            "delete_interview",
            "set_pass_mark",
            "set_question_seconds",
            "keep_questions_private",
            "set_topic_limit",
            "list_topic_questions",
            "regenerate_question",
            "mark_question_wrong",
            "list_question_reports",
            "set_interview_link",
            "get_generation",
            "review_generation",
            "retry_generation",
            "cancel_generation",
        }
    ),
    ToolGroup.TEMPLATES_PRACTICE: frozenset(
        {
            "search_templates",
            "list_copyable_templates",
            "list_template_filters",
            "get_template",
            "start_practice",
            "list_practice_rounds",
            "get_practice_progress",
        }
    ),
    ToolGroup.TEAM_COMPANY: frozenset(
        {
            "list_members",
            "invite_member",
            "change_member_role",
            "remove_member",
            "create_company",
            "rename_company",
            "delete_company",
            "set_company_website",
            "remove_company_logo",
            "list_company_actions",
        }
    ),
    ToolGroup.BILLING: frozenset(
        {
            "get_credits",
            "list_company_balances",
            "list_credit_history",
            "list_reserved_credits",
            "get_auto_top_up",
            "turn_off_auto_top_up",
            "get_price_catalog",
            "get_referral",
            "get_faq",
        }
    ),
    ToolGroup.INTEGRATIONS: frozenset(
        {
            "list_ats_connections",
            "list_ats_jobs",
            "list_ats_links",
            "list_ats_stages",
            "get_ats_job_text",
            "link_ats_job",
            "unlink_ats_job",
            "disconnect_ats",
            "retry_ats_candidates",
            "get_slack",
            "set_slack_kinds",
            "disconnect_slack",
            "get_api_settings",
            "create_webhook",
            "remove_webhook",
            "remove_api_key",
        }
    ),
    ToolGroup.ACCOUNT: frozenset(
        {
            "get_email_preferences",
            "update_email_preferences",
            "update_language",
            "delete_account",
            "list_notifications",
            "mark_notifications_seen",
            "list_news",
            "get_pause",
        }
    ),
}
