"""update_checks: when each AI app connection (OAuth grant) or API key last called get_updates,
so its next call tells what came since

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "update_checks",
        sa.Column("connection_id", sa.String(64), primary_key=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("update_checks")
