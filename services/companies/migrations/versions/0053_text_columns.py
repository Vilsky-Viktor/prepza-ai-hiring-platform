"""Text instead of varchar(n) where the length was no rule: lengths the API sets
(MAX_COMPANY_NAME_LENGTH) or the code makes, not the column. varchar to text rewrites no table;
only the index on lower(name) is rebuilt (its expression loses a cast), on a row per company

Revision ID: 0053
Revises: 0052
Create Date: 2026-10-21
"""

from alembic import op

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (
    ("companies", "name", 200),
    ("companies", "verification_name", 200),
    ("candidate_invites", "hold_key", 200),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: binary coercible, no rewrite (see above)
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
