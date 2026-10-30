"""auto_top_up_on joins ck_notifications_kind (NOT VALID, then validated in its own
transaction): turning automatic top-up on is confirmed in the bell and by email

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-30
"""

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

NAME = "ck_notifications_kind"
BEFORE = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'auto_top_up_paused', 'auto_top_up_price_change', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'note_added', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"
NOW = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_on', 'auto_top_up_charged', 'auto_top_up_failed', 'auto_top_up_paused', 'auto_top_up_price_change', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'note_added', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"


def swap(condition: str) -> None:
    op.execute(f"ALTER TABLE notifications DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE notifications ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    swap(NOW)

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE notifications VALIDATE CONSTRAINT {NAME}")


def downgrade() -> None:
    op.execute("DELETE FROM notifications WHERE kind = 'auto_top_up_on'")
    swap(BEFORE)
