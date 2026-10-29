"""The stale api_key_narrowed action goes: its rows read as api_key_permissions_changed, which
replaced it, and the action CHECK is replaced without it, added NOT VALID and validated in its
own transaction

Revision ID: 0069
Revises: 0068
Create Date: 2026-10-30
"""

from alembic import op

revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None

NAME = "ck_audit_events_action"
BEFORE = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'note_added', 'note_edited', 'note_deleted', 'note_pinned', 'note_unpinned', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_permissions_changed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"
AFTER = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'note_added', 'note_edited', 'note_deleted', 'note_pinned', 'note_unpinned', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_permissions_changed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"


def replace(condition: str) -> None:
    op.execute(f"ALTER TABLE audit_events DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE audit_events ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE audit_events VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    op.execute(
        "UPDATE audit_events SET action = 'api_key_permissions_changed' "
        "WHERE action = 'api_key_narrowed'"
    )
    replace(AFTER)


def downgrade() -> None:
    replace(BEFORE)
