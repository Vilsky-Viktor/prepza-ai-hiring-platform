"""quality_patterns.eval_run: the eval gate's run that put a pattern in use (its date, commit and
results file), so the admin zone shows what a rule in use was measured on. One nullable column,
added without a default: instant.

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quality_patterns", sa.Column("eval_run", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("quality_patterns", "eval_run")
