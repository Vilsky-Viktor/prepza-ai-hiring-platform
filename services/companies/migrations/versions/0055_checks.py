"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes

Revision ID: 0055
Revises: 0054
Create Date: 2026-10-21
"""

from alembic import op

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    (
        "audit_events",
        "ck_audit_events_action",
        "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'webhook_added', 'webhook_tested', 'webhook_deleted')",
    ),
    (
        "audit_events",
        "ck_audit_events_group",
        "\"group\" IN ('interviews', 'candidates', 'team', 'company', 'billing', 'integrations')",
    ),
    (
        "audit_events",
        "ck_audit_events_target_kind",
        "target_kind IN ('candidate', 'interview', 'member', 'company', 'api_key', 'webhook', 'integration')",
    ),
    ("audit_events", "ck_audit_events_via", "via IN ('assistant', 'mcp', 'api', 'ats')"),
    ("candidate_invites", "ck_candidate_invites_extra_time", "extra_time >= 0"),
    ("candidate_invites", "ck_candidate_invites_grade", "grade BETWEEN 0 AND 100"),
    (
        "candidate_invites",
        "ck_candidate_invites_status",
        "status IN ('invited', 'undelivered', 'in_process', 'finished', 'deleted', 'expired')",
    ),
    ("candidate_invites", "ck_candidate_invites_theme", "theme IN ('light', 'dark')"),
    (
        "companies",
        "ck_companies_brand_font",
        "brand_font IN ('poppins_geist', 'inter', 'roboto', 'open_sans', 'lato', 'montserrat', 'nunito', 'raleway', 'work_sans', 'source_sans_3', 'noto_sans', 'pt_sans', 'ubuntu', 'rubik', 'manrope', 'dm_sans', 'ibm_plex_sans', 'mulish', 'fira_sans', 'plus_jakarta_sans', 'outfit', 'merriweather', 'lora', 'playfair_display')",
    ),
    ("companies", "ck_companies_logo_type", "logo_type IN ('image/jpeg', 'image/png')"),
    (
        "companies",
        "ck_companies_verification_status",
        "verification_status IN ('none', 'waiting_email', 'pending', 'approved', 'declined')",
    ),
    ("interviews", "ck_interviews_pass_mark", "pass_mark BETWEEN 0 AND 100"),
    ("interviews", "ck_interviews_question_seconds", "question_seconds > 0"),
    ("members", "ck_members_role", "role IN ('owner', 'admin', 'viewer')"),
)
NOT_YET = ()


def upgrade() -> None:
    for table, name, condition in CHECKS:
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        for table, name, _ in CHECKS:
            if name not in NOT_YET:
                op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")


def downgrade() -> None:
    for table, name, _ in CHECKS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
