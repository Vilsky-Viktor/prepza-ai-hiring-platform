"""created_at defaults to now() in the database too, so a row written outside the ORM (raw SQL,
a backfill, another client) gets it. Setting a default changes only the catalog

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-21
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

TABLES = ("outbox", "purchases")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at SET DEFAULT now()")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at DROP DEFAULT")
