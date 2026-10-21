"""candidate_invites.pledged_at: when the candidate confirmed, before starting, that they'd answer
on their own, without AI tools or other people; the scorecard shows it

Revision ID: 0051
Revises: 0050
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_invites", sa.Column("pledged_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_invites", "pledged_at")
