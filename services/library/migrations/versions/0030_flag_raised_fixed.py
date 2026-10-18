"""question_stats.flag_raised_at and question_revisions.fixed: when a question was newly
flagged, and whether a replacement fixed a flagged question, so the assistant's get_updates
tells each once

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_stats", sa.Column("flag_raised_at", sa.DateTime(timezone=True)))
    op.add_column(
        "question_revisions",
        sa.Column("fixed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("question_revisions", "fixed")
    op.drop_column("question_stats", "flag_raised_at")
