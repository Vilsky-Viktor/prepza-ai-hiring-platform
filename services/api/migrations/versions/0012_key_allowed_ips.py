"""An API key may be limited to the addresses its servers call from (IPv4 or IPv6, single or
CIDR ranges); empty, as every existing key gets, means any. One column with a constant default:
instant on Postgres 11 and later

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column(
            "allowed_ips",
            postgresql.ARRAY(sa.String(length=49)),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "allowed_ips")
