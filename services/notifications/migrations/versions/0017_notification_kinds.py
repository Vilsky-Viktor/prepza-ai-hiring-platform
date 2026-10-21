"""ck_notifications_kind allows the kinds added since it was made (an automatic top-up paused, its
price changing): the database refused their notifications. Swapped NOT VALID, as before, so it
takes the table's lock only for a moment

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-22
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

NAME = "ck_notifications_kind"
NOW = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'auto_top_up_paused', 'auto_top_up_price_change', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'webhook_stopped', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"
BEFORE = "kind IN ('question_flagged', 'question_fixed', 'referral_rewarded', 'auto_top_up_charged', 'auto_top_up_failed', 'candidate_finished', 'invite_undelivered', 'interview_ready', 'interview_cancelled', 'ats_not_invited', 'ats_cannot_write', 'connection_broken', 'webhook_stopped', 'member_joined', 'ownership_received', 'verification_approved', 'verification_declined', 'news', 'legal_terms', 'legal_privacy', 'legal_dpa')"


def swap(condition: str) -> None:
    op.execute(f"ALTER TABLE notifications DROP CONSTRAINT {NAME}")
    op.execute(f"ALTER TABLE notifications ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID")


def upgrade() -> None:
    swap(NOW)


def downgrade() -> None:
    swap(BEFORE)
