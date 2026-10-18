"""ats_candidates.failed_at: when a candidate the ATS sent first couldn't be invited, so the
assistant's get_updates tells each one once

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ats_candidates", sa.Column("failed_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("ats_candidates", "failed_at")
