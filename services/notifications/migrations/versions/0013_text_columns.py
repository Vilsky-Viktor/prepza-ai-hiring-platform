"""Text instead of varchar(n) where the length was no rule: Slack's workspace and channel names,
whose length nothing checked (a longer one failed the connection), and keys with no length rule.
varchar to text rewrites neither the table nor its indexes, so it only changes the catalog

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-21
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (
    ("slack_connections", "team", 200),
    ("slack_connections", "channel", 200),
    ("bulk_sends", "about", 64),
    ("sent_emails", "key", 160),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
