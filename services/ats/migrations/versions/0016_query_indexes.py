"""Indexes for the recovery job's candidates, the kept results and the candidates who couldn't be
invited, which read every candidate of a connection; three indexes another one already covers
go. Built and dropped concurrently, so writes go on meanwhile

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-21
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (
    (
        "ix_ats_candidates_waiting",
        "ats_candidates (connection_id, created_at) WHERE status IN ('waiting', 'inviting')",
    ),
    (
        "ix_ats_candidates_unreported",
        "ats_candidates (connection_id, kept_at) WHERE result IS NOT NULL AND reported_at IS NULL",
    ),
    (
        "ix_ats_candidates_failed",
        "ats_candidates (connection_id, failed_at) WHERE status = 'failed'",
    ),
)
DROPPED = (
    ("ix_ats_candidates_connection_id", "ats_candidates (connection_id)"),
    ("ix_ats_job_links_connection_id", "ats_job_links (connection_id)"),
    ("ix_ats_connections_company_id", "ats_connections (company_id)"),
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for name, target in CREATED:
            # A build cut off earlier leaves an invalid index of this name: built again.
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE INDEX CONCURRENTLY {name} ON {target}")

        for name, _ in DROPPED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _ in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")

        for name, target in DROPPED:
            op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {target}")
