"""Text instead of varchar(n) where the length was no rule: an id with no length rule. varchar to
text rewrites neither the table nor its indexes, so it only changes the catalog

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-21
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (("key_checks", "batch_id", 64),)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
