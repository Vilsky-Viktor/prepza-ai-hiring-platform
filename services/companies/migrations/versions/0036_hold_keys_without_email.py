"""candidate_invites hold_key: every invite has its own, without the candidate's email
("{interview_id}:{hash}", as billing migration 0011 rewrites its keys), and an index for
billing's history

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-11
"""

from alembic import op
from testee_common.limits.credit_keys import invite_key

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None

# The old key: the stored one, or "{interview_id}:{email}" on invites made before each had one.
OLD_KEY = "coalesce(hold_key, interview_id::text || ':' || lower(email))"
# The new one: "{interview_id}:" and a hash of the old key, as billing's migration 0011 makes it.
NEW_KEY = invite_key("interview_id", OLD_KEY)


def upgrade() -> None:
    op.execute(f"UPDATE candidate_invites SET hold_key = {NEW_KEY}")
    op.alter_column("candidate_invites", "hold_key", nullable=False)
    op.create_index("ix_candidate_invites_hold_key", "candidate_invites", ["hold_key"])


def downgrade() -> None:
    op.drop_index("ix_candidate_invites_hold_key", "candidate_invites")
    op.alter_column("candidate_invites", "hold_key", nullable=True)
