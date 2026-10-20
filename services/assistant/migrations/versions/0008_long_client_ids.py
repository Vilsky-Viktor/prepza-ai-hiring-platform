"""oauth_clients.client_id and mcp_grants.client_id up to 512 characters: an AI app that names
itself by its Client ID Metadata Document uses that document's HTTPS address as its client_id.

Widening a varchar is the one type change Postgres makes without rewriting or rescanning the
table (a catalogue change under a brief lock, bounded by the migration's lock_timeout), so it's
done in place rather than through a new column; the code before this keeps working on it.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-20
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("oauth_clients", "mcp_grants"):
        op.alter_column(table, "client_id", type_=sa.String(512), existing_type=sa.String(64))


def downgrade() -> None:
    for table in ("mcp_grants", "oauth_clients"):
        op.alter_column(table, "client_id", type_=sa.String(64), existing_type=sa.String(512))
