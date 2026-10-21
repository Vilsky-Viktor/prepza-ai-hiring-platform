"""Text instead of varchar(n) where the length was no rule: names and ids an ATS sends, whose
length nothing checked: a longer one failed its request. varchar to text rewrites neither the
table nor its indexes, so it only changes the catalog

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-21
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

# (table, column, its length before)
COLUMNS = (
    ("ats_connections", "account", 200),
    ("ats_connections", "member_id", 100),
    ("ats_job_links", "job_name", 300),
    ("ats_job_links", "stage_name", 200),
    ("ats_job_links", "subscription_id", 100),
    ("ats_candidates", "candidate_id", 100),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: varchar to text is binary coercible: no rewrite, no index rebuild
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text")


def downgrade() -> None:
    for table, column, length in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE varchar({length})")
