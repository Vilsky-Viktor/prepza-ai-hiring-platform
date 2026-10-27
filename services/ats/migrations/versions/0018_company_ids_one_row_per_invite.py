"""Every tenant's row carries its company: ats_job_links and ats_candidates get company_id from
their connection, filled in batches, indexed and NOT NULL. And an invite belongs to one ATS row
(uq_ats_candidates_invite_id, built concurrently, replacing the plain index), the one whose
results go back

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-22
"""

from alembic import op
from prepza_common.db.tenant_columns import add_company_id, drop_company_id

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

TABLES = {
    table: (
        f"UPDATE {table} t SET company_id = c.company_id FROM ats_connections c "
        f"WHERE c.id = t.connection_id AND t.ctid IN "
        f"(SELECT ctid FROM {table} WHERE company_id IS NULL LIMIT 1000)"
    )
    for table in ("ats_job_links", "ats_candidates")
}


def upgrade() -> None:
    for table, fill in TABLES.items():
        add_company_id(op, table, fill)

    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS uq_ats_candidates_invite_id")
        op.execute(
            "CREATE UNIQUE INDEX CONCURRENTLY uq_ats_candidates_invite_id "
            "ON ats_candidates (invite_id)"
        )
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_ats_candidates_invite_id")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_ats_candidates_invite_id "
            "ON ats_candidates (invite_id)"
        )
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS uq_ats_candidates_invite_id")

    for table in TABLES:
        drop_company_id(op, table)
