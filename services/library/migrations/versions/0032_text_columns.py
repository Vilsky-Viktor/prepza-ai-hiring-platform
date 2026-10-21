"""Text instead of varchar(n) where the length was no rule: lengths the API sets (MAX_TITLE_LENGTH,
SLUG_LENGTH), not the column. varchar to text rewrites neither the table nor its indexes, so it
only changes the catalog

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-21
"""

from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (
    ("sets", "title", 200),
    ("sets", "slug", 120),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
