"""Money only as an integer: the text `total` columns go, after copying any row written with
only the text since 0020, and every purchase has its total (`total_minor` NOT NULL). An entry
that moved no money (a gift, a charge) keeps NULL.

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

TABLES = ("entries", "purchases")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")

    for table in TABLES:
        op.execute(
            f"UPDATE {table} SET total_minor = total::bigint "
            "WHERE total_minor IS NULL AND total ~ '^[0-9]+$'"
        )
        op.drop_column(table, "total")

    op.alter_column("purchases", "total_minor", nullable=False)


def downgrade() -> None:
    op.alter_column("purchases", "total_minor", nullable=True)

    for table in TABLES:
        op.add_column(table, sa.Column("total", sa.Text(), nullable=True))
        op.execute(f"UPDATE {table} SET total = total_minor::text")
