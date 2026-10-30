"""The team's notes notify: note_added joins ck_notifications_kind (NOT VALID, then validated in
its own transaction), the bell finds a member's grouped notes by their interview, the digest keeps
each new note in pending_notes, and every connected Slack channel gets notes, as the user decided

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

NAME = "ck_notifications_kind"
BEFORE = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'auto_top_up_paused', 'auto_top_up_price_change', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"
NOW = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'auto_top_up_paused', 'auto_top_up_price_change', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'note_added', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"


def swap(condition: str) -> None:
    op.execute(f"ALTER TABLE notifications DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE notifications ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    swap(NOW)
    op.create_table(
        "pending_notes",
        sa.Column("note_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("company_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("interview_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("author_id", sa.String(128), nullable=True),
        sa.Column("author_name", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_pending_notes_company_created", "pending_notes", ["company_id", "created_at"]
    )
    op.create_index("ix_pending_notes_interview", "pending_notes", ["interview_id"])
    # migration-check: slack_connections has one row per company with Slack, a few rows.
    op.execute(
        "UPDATE slack_connections SET kinds = kinds || '[\"note_added\"]'::jsonb "
        "WHERE NOT kinds ? 'note_added'"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE notifications VALIDATE CONSTRAINT {NAME}")
        op.create_index(
            "ix_notifications_note_interview",
            "notifications",
            [sa.text("(data ->> 'interview_id')")],
            postgresql_where=sa.text("kind = 'note_added'"),
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    op.drop_index("ix_notifications_note_interview", table_name="notifications")
    op.drop_table("pending_notes")
    op.execute("DELETE FROM notifications WHERE kind = 'note_added'")
    op.execute("UPDATE slack_connections SET kinds = kinds - 'note_added'")
    swap(BEFORE)
