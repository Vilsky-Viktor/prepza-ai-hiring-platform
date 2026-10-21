"""created_at defaults to now() in the database too, so a row written outside the ORM (raw SQL,
a backfill, another client) gets it. Setting a default changes only the catalog

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-21
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

TABLES = ("ats_candidates", "ats_connections", "ats_job_links", "outbox")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at SET DEFAULT now()")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at DROP DEFAULT")
