"""candidate_invites.undelivered_at: when the invite email last bounced or was marked as spam,
so the assistant's get_updates tells each undelivered invite once

Revision ID: 0049
Revises: 0048
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_invites", sa.Column("undelivered_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_invites", "undelivered_at")
