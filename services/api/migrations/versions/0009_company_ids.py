"""Every tenant's row carries its company: webhook_deliveries, webhook_retries and
webhook_attempts get company_id from their web hook, filled in batches, indexed and NOT NULL

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-22
"""

from alembic import op
from testee_common.db.tenant_columns import add_company_id, drop_company_id

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

# Each table, and how a batch of its empty rows is filled from its web hook.
TABLES = {
    table: (
        f"UPDATE {table} t SET company_id = w.company_id FROM webhooks w "
        f"WHERE w.id = t.webhook_id AND t.ctid IN "
        f"(SELECT ctid FROM {table} WHERE company_id IS NULL LIMIT 1000)"
    )
    for table in ("webhook_deliveries", "webhook_retries", "webhook_attempts")
}


def upgrade() -> None:
    for table, fill in TABLES.items():
        add_company_id(op, table, fill)


def downgrade() -> None:
    for table in TABLES:
        drop_company_id(op, table)
