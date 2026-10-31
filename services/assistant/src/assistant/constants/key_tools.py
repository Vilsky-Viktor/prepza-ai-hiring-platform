# AI agents signed in to the MCP server with a company's API key (`te_...`) get only the tools
# their key's permissions allow (the api service's src/api/constants/permissions.py): each tool
# here and the permission it needs. KEY_ONLY_MCP needs nothing beyond the mcp permission itself: the
# key's company, the platform's pause, its guides and prices. Any other tool (the team, brand,
# settings, billing, integrations, the account) isn't listed for keys.

KEY_ONLY_MCP = "mcp"
INTERVIEWS_READ = "interviews:read"
INTERVIEWS_CREATE = "interviews:create"
CANDIDATES_READ = "candidates:read"
CANDIDATES_INVITE = "candidates:invite"
CANDIDATES_CHANGE = "candidates:change"
CANDIDATES_DELETE = "candidates:delete"
NOTES_READ = "notes:read"
NOTES_ADD = "notes:add"
CREDITS_READ = "credits:read"

KEY_TOOLS = {
    "list_companies": KEY_ONLY_MCP,
    "get_company": KEY_ONLY_MCP,
    "get_pause": KEY_ONLY_MCP,
    "get_faq": KEY_ONLY_MCP,
    "get_platform_guide": KEY_ONLY_MCP,
    "list_guides": KEY_ONLY_MCP,
    "get_guide": KEY_ONLY_MCP,
    "get_price_catalog": KEY_ONLY_MCP,
    "list_interviews": INTERVIEWS_READ,
    "get_interview": INTERVIEWS_READ,
    "get_generation": INTERVIEWS_READ,
    "list_topic_questions": INTERVIEWS_READ,
    "list_question_reports": INTERVIEWS_READ,
    "create_interview": INTERVIEWS_CREATE,
    "create_interview_from_template": INTERVIEWS_CREATE,
    "review_generation": INTERVIEWS_CREATE,
    "retry_generation": INTERVIEWS_CREATE,
    "cancel_generation": INTERVIEWS_CREATE,
    "search_templates": INTERVIEWS_CREATE,
    "list_template_filters": INTERVIEWS_CREATE,
    "get_template": INTERVIEWS_CREATE,
    "list_copyable_templates": INTERVIEWS_CREATE,
    "list_candidates": CANDIDATES_READ,
    "search_candidates": CANDIDATES_READ,
    "get_scorecard": CANDIDATES_READ,
    "get_interview_report": CANDIDATES_READ,
    "get_updates": CANDIDATES_READ,
    "invite_candidate": CANDIDATES_INVITE,
    "invite_candidates": CANDIDATES_INVITE,
    "rename_candidate": CANDIDATES_CHANGE,
    "set_extra_time": CANDIDATES_CHANGE,
    "revoke_candidate": CANDIDATES_DELETE,
    "list_interview_notes": NOTES_READ,
    "add_interview_note": NOTES_ADD,
    "get_credits": CREDITS_READ,
    "list_company_balances": CREDITS_READ,
}
