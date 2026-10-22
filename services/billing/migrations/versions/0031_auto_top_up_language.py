"""auto_top_ups.language: each automatic charge's item is named on Paddle's invoice in the
language of whoever turned it on. Nullable: rows from before are named in English

Revision ID: 0031
Revises: 0030
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("auto_top_ups", sa.Column("language", sa.String(8), nullable=True))


def downgrade() -> None:
    op.drop_column("auto_top_ups", "language")
