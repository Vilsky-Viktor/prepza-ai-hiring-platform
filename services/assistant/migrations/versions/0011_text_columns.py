"""Text instead of varchar(n) where the length was no rule: an AI app's client id (a URL of any
length, unchecked: a longer one failed its sign-in) and a connection's id. varchar to text
rewrites neither the table nor its indexes, so it only changes the catalog

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-21
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (
    ("oauth_clients", "client_id", 512),
    ("mcp_grants", "client_id", 512),
    ("update_checks", "connection_id", 64),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
