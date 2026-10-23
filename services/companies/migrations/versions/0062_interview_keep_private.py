"""An interview can be kept out of prepza's shared question bank (keep_private), the opt-out the
2026-11-08 terms promise; off by default, so a constant default makes the column instant

Revision ID: 0062
Revises: 0061
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0062"
down_revision = "0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("keep_private", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("interviews", "keep_private")
