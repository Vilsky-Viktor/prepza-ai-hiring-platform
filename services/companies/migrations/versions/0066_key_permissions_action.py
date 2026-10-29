"""The action log takes an API key's permissions being changed (api_key_permissions_changed),
now that they can be added as well as taken away; api_key_narrowed stays for older rows. The
action CHECK is replaced with one that names it, added NOT VALID and validated in its own
transaction, which reads the rows without blocking writes

Revision ID: 0066
Revises: 0065
Create Date: 2026-10-29
"""

from alembic import op

revision = "0066"
down_revision = "0065"
branch_labels = None
depends_on = None

NAME = "ck_audit_events_action"
BEFORE = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"
AFTER = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_permissions_changed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"


def replace(condition: str) -> None:
    op.execute(f"ALTER TABLE audit_events DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE audit_events ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE audit_events VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    replace(AFTER)


def downgrade() -> None:
    replace(BEFORE)
