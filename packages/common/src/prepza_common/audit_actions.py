# What a company's action log records (companies' audit_events): every action a member takes on
# the company, by group (the log's action filter). Companies records its own; billing, ats,
# notifications and api send theirs as AUDIT_RECORDED events through their outbox (audit.py).
from enum import StrEnum

# Another service's action, for companies to store in the company's log.
AUDIT_RECORDED = "audit.recorded"


class AuditGroup(StrEnum):
    INTERVIEWS = "interviews"
    CANDIDATES = "candidates"
    TEAM = "team"
    COMPANY = "company"
    BILLING = "billing"
    INTEGRATIONS = "integrations"


class TargetKind(StrEnum):
    """What an action was about. People (candidates, members) are looked up when the log is
    read, never kept in it; anything else keeps its label as it was (an interview's title)."""

    CANDIDATE = "candidate"
    INTERVIEW = "interview"
    MEMBER = "member"
    COMPANY = "company"
    API_KEY = "api_key"
    WEBHOOK = "webhook"
    INTEGRATION = "integration"


class AuditAction(StrEnum):
    # Interviews.
    INTERVIEW_CREATED = "interview_created"
    INTERVIEW_FROM_TEMPLATE = "interview_from_template"
    INTERVIEW_DELETED = "interview_deleted"
    INTERVIEW_RENAMED = "interview_renamed"
    INTERVIEW_SETTINGS_CHANGED = "interview_settings_changed"
    LINK_TURNED_ON = "link_turned_on"
    LINK_TURNED_OFF = "link_turned_off"
    QUESTIONS_REGENERATED = "questions_regenerated"
    ANSWER_KEY_REPORTED = "answer_key_reported"
    TOPICS_APPROVED = "topics_approved"
    PASS_MARK_CHANGED = "pass_mark_changed"
    # Candidates.
    CANDIDATE_INVITED = "candidate_invited"
    INVITE_RESENT = "invite_resent"
    INVITE_REVOKED = "invite_revoked"
    CANDIDATE_DELETED = "candidate_deleted"
    CANDIDATE_RENAMED = "candidate_renamed"
    EXTRA_TIME_SET = "extra_time_set"
    RESULTS_VIEWED = "results_viewed"
    REPORT_EMAILED = "report_emailed"
    # Team.
    MEMBER_INVITED = "member_invited"
    MEMBER_JOINED = "member_joined"
    MEMBER_REMOVED = "member_removed"
    MEMBER_ROLE_CHANGED = "member_role_changed"
    OWNERSHIP_TRANSFERRED = "ownership_transferred"
    # The company.
    COMPANY_RENAMED = "company_renamed"
    LOGO_CHANGED = "logo_changed"
    BRAND_CHANGED = "brand_changed"
    VERIFICATION_REQUESTED = "verification_requested"
    AI_APPS_CHANGED = "ai_apps_changed"
    # Billing.
    TOP_UP_PAID = "top_up_paid"
    AUTO_TOP_UP_SET = "auto_top_up_set"
    AUTO_TOP_UP_CHANGED = "auto_top_up_changed"
    AUTO_TOP_UP_STOPPED = "auto_top_up_stopped"
    CURRENCY_CHANGED = "currency_changed"
    # Integrations.
    ATS_CONNECTED = "ats_connected"
    ATS_RECONNECTED = "ats_reconnected"
    ATS_DISCONNECTED = "ats_disconnected"
    JOB_LINKED = "job_linked"
    JOB_UNLINKED = "job_unlinked"
    SLACK_CONNECTED = "slack_connected"
    SLACK_DISCONNECTED = "slack_disconnected"
    SLACK_NOTIFICATIONS_CHANGED = "slack_notifications_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    API_KEY_NARROWED = "api_key_narrowed"
    WEBHOOK_ADDED = "webhook_added"
    WEBHOOK_TESTED = "webhook_tested"
    WEBHOOK_DELETED = "webhook_deleted"


_GROUPS = {
    AuditGroup.INTERVIEWS: (
        AuditAction.INTERVIEW_CREATED,
        AuditAction.INTERVIEW_FROM_TEMPLATE,
        AuditAction.INTERVIEW_DELETED,
        AuditAction.INTERVIEW_RENAMED,
        AuditAction.INTERVIEW_SETTINGS_CHANGED,
        AuditAction.LINK_TURNED_ON,
        AuditAction.LINK_TURNED_OFF,
        AuditAction.QUESTIONS_REGENERATED,
        AuditAction.ANSWER_KEY_REPORTED,
        AuditAction.TOPICS_APPROVED,
        AuditAction.PASS_MARK_CHANGED,
    ),
    AuditGroup.CANDIDATES: (
        AuditAction.CANDIDATE_INVITED,
        AuditAction.INVITE_RESENT,
        AuditAction.INVITE_REVOKED,
        AuditAction.CANDIDATE_DELETED,
        AuditAction.CANDIDATE_RENAMED,
        AuditAction.EXTRA_TIME_SET,
        AuditAction.RESULTS_VIEWED,
        AuditAction.REPORT_EMAILED,
    ),
    AuditGroup.TEAM: (
        AuditAction.MEMBER_INVITED,
        AuditAction.MEMBER_JOINED,
        AuditAction.MEMBER_REMOVED,
        AuditAction.MEMBER_ROLE_CHANGED,
        AuditAction.OWNERSHIP_TRANSFERRED,
    ),
    AuditGroup.COMPANY: (
        AuditAction.COMPANY_RENAMED,
        AuditAction.LOGO_CHANGED,
        AuditAction.BRAND_CHANGED,
        AuditAction.VERIFICATION_REQUESTED,
        AuditAction.AI_APPS_CHANGED,
    ),
    AuditGroup.BILLING: (
        AuditAction.TOP_UP_PAID,
        AuditAction.AUTO_TOP_UP_SET,
        AuditAction.AUTO_TOP_UP_CHANGED,
        AuditAction.AUTO_TOP_UP_STOPPED,
        AuditAction.CURRENCY_CHANGED,
    ),
    AuditGroup.INTEGRATIONS: (
        AuditAction.ATS_CONNECTED,
        AuditAction.ATS_RECONNECTED,
        AuditAction.ATS_DISCONNECTED,
        AuditAction.JOB_LINKED,
        AuditAction.JOB_UNLINKED,
        AuditAction.SLACK_CONNECTED,
        AuditAction.SLACK_DISCONNECTED,
        AuditAction.SLACK_NOTIFICATIONS_CHANGED,
        AuditAction.API_KEY_CREATED,
        AuditAction.API_KEY_DELETED,
        AuditAction.API_KEY_NARROWED,
        AuditAction.WEBHOOK_ADDED,
        AuditAction.WEBHOOK_TESTED,
        AuditAction.WEBHOOK_DELETED,
    ),
}

# Each action's group, the column the log's action filter looks up.
ACTION_GROUPS = {action: group for group, actions in _GROUPS.items() for action in actions}

# A label kept for what an action was about (an interview's title, a web hook's host) is cut to
# this length.
MAX_TARGET_LABEL = 256
