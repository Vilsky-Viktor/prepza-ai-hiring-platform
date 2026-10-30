"""auto_top_ups.agreed_at: when the person whose card pays last agreed to the automatic top-up's
terms, kept as long as it runs. Nullable: rows from before weren't asked

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("auto_top_ups", sa.Column("agreed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("auto_top_ups", "agreed_at")
