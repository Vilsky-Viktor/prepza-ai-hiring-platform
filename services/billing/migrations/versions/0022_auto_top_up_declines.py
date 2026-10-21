"""Automatic top-up stops retrying a declined card past the card networks' limits: how many
declines in a row, when to try again, and when it was paused until the card is updated.

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

TIMES = ("retry_at", "paused_at")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.add_column(
        "auto_top_ups",
        sa.Column("declines", sa.Integer(), server_default="0", nullable=False),
    )

    for column in TIMES:
        op.add_column("auto_top_ups", sa.Column(column, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for column in ("declines", *TIMES):
        op.drop_column("auto_top_ups", column)
