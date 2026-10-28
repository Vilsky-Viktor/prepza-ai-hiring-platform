"""A company's allowed domains: the sites that may embed its interviews and that the API's
return_url may lead to, and whether localhost may too, apart from verification (which now only
gives the badge). A verified company keeps what it had: its domain and its subdomains. The
action log takes the list being changed (embed_domains_changed): the action CHECK is replaced,
added NOT VALID and validated in its own transaction

Revision ID: 0065
Revises: 0064
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0065"
down_revision = "0064"
branch_labels = None
depends_on = None

NAME = "ck_audit_events_action"
BEFORE = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"
AFTER = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"


def replace(condition: str) -> None:
    op.execute(f"ALTER TABLE audit_events DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE audit_events ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE audit_events VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "allowed_domains",
            postgresql.ARRAY(sa.String(length=260)),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "companies",
        sa.Column("allow_localhost", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute(
        "UPDATE companies SET allowed_domains = ARRAY[verified_domain, '*.' || verified_domain] "
        "WHERE verified_domain IS NOT NULL"
    )
    replace(AFTER)


def downgrade() -> None:
    replace(BEFORE)
    op.drop_column("companies", "allow_localhost")
    op.drop_column("companies", "allowed_domains")
