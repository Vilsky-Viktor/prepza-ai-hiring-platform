"""Indexes for what read whole tables: a person's invites and action log entries by email or
account (deletion, export), invites by when they were sent (expiry, reminders, retention),
member invites by address, interviews by when they were ready or started (reminder emails), and
an interview's candidates newest first; two indexes another one already covers go. Built and
dropped concurrently, so writes go on meanwhile

Revision ID: 0054
Revises: 0053
Create Date: 2026-10-21
"""

from alembic import op

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (
    ("ix_candidate_invites_interview_created", "candidate_invites (interview_id, created_at, id)"),
    ("ix_candidate_invites_email", "candidate_invites (email)"),
    ("ix_candidate_invites_sent_at", "candidate_invites (sent_at)"),
    ("ix_audit_events_user_id", "audit_events (user_id)"),
    ("ix_members_invited_email", "members (invited_email)"),
    ("ix_interviews_ready_at", "interviews (ready_at)"),
    ("ix_interviews_created_at", "interviews (created_at)"),
)
DROPPED = (
    ("ix_candidate_invites_interview_id", "candidate_invites (interview_id)"),
    ("ix_interviews_company_id", "interviews (company_id)"),
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for name, target in CREATED:
            # A build cut off earlier leaves an invalid index of this name: built again.
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE INDEX CONCURRENTLY {name} ON {target}")

        for name, _ in DROPPED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _ in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")

        for name, target in DROPPED:
            op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {target}")
