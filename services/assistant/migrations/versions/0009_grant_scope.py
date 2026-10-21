"""mcp_grants.scope: what the user allowed an AI app, everything (`prepza`) or only reading
(`prepza:read`). Connections made before keep everything, as they were allowed then (a constant
default, added without rewriting the table).

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-20
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mcp_grants",
        sa.Column("scope", sa.String(32), nullable=False, server_default="prepza"),
    )


def downgrade() -> None:
    op.drop_column("mcp_grants", "scope")
