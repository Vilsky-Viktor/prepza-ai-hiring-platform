"""A start marks the invite while it makes the candidate's sessions
(candidate_invites.starting_at), so a change to their extra time or mode saved meanwhile is
refused instead of missing their sessions. A nullable column without a default, instant to add

Revision ID: 0073
Revises: 0072
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0073"
down_revision = "0072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_invites", sa.Column("starting_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_invites", "starting_at")
