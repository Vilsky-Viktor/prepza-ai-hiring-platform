"""An interview's notes: what its team writes about the hiring round (interview_notes), deleted
with the interview and the company, a former member's kept without their membership. The action
log takes writing, editing, deleting and pinning one: the action CHECK is replaced, added NOT
VALID and validated in its own transaction

Revision ID: 0068
Revises: 0067
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0068"
down_revision = "0067"
branch_labels = None
depends_on = None

NAME = "ck_audit_events_action"
BEFORE = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_permissions_changed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"
AFTER = "action IN ('interview_created', 'interview_from_template', 'interview_deleted', 'interview_renamed', 'interview_settings_changed', 'link_turned_on', 'link_turned_off', 'questions_regenerated', 'answer_key_reported', 'topics_approved', 'pass_mark_changed', 'note_added', 'note_edited', 'note_deleted', 'note_pinned', 'note_unpinned', 'candidate_invited', 'invite_resent', 'invite_revoked', 'candidate_deleted', 'candidate_renamed', 'extra_time_set', 'results_viewed', 'report_emailed', 'member_invited', 'member_joined', 'member_removed', 'member_role_changed', 'ownership_transferred', 'company_renamed', 'logo_changed', 'brand_changed', 'verification_requested', 'ai_apps_changed', 'embed_domains_changed', 'top_up_paid', 'auto_top_up_set', 'auto_top_up_changed', 'auto_top_up_stopped', 'currency_changed', 'ats_connected', 'ats_reconnected', 'ats_disconnected', 'job_linked', 'job_unlinked', 'slack_connected', 'slack_disconnected', 'slack_notifications_changed', 'api_key_created', 'api_key_deleted', 'api_key_narrowed', 'api_key_permissions_changed', 'api_key_ips_changed', 'webhook_added', 'webhook_tested', 'webhook_deleted', 'webhook_secret_rotated')"


def replace(condition: str) -> None:
    op.execute(f"ALTER TABLE audit_events DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE audit_events ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE audit_events VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    op.create_table(
        "interview_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("author_member_id", sa.Uuid(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("pinned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(text) BETWEEN 1 AND 2000", name="ck_interview_notes_text"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_member_id"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_notes_company_id", "interview_notes", ["company_id"])
    op.create_index("ix_interview_notes_author_member_id", "interview_notes", ["author_member_id"])
    op.create_index(
        "ix_interview_notes_interview_created", "interview_notes", ["interview_id", "created_at"]
    )
    op.create_index(
        "uq_interview_notes_pinned",
        "interview_notes",
        ["interview_id"],
        unique=True,
        postgresql_where=sa.text("pinned"),
    )
    replace(AFTER)


def downgrade() -> None:
    replace(BEFORE)
    op.drop_table("interview_notes")
