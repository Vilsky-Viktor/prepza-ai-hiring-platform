"""messages.trace_id and messages.vote: an answer's Langfuse trace (null when Langfuse wasn't
set up) and its owner's thumbs up (1) or down (-1), null when there's none

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("trace_id", sa.String(32)))
    op.add_column("messages", sa.Column("vote", sa.SmallInteger()))


def downgrade() -> None:
    op.drop_column("messages", "vote")
    op.drop_column("messages", "trace_id")
