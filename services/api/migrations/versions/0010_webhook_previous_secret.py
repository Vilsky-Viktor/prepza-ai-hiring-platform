"""A web hook's secret can be rolled without losing events: the one it replaced (encrypted)
keeps signing too until previous_until. Two nullable columns, added without a default: instant

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("webhooks", sa.Column("previous_secret", sa.Text(), nullable=True))
    op.add_column(
        "webhooks", sa.Column("previous_until", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("webhooks", "previous_until")
    op.drop_column("webhooks", "previous_secret")
