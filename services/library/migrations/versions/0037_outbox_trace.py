"""Each outbox event keeps the trace of the request that saved it, sent with it to Pub/Sub, so
its consumers' logs join that request's. One nullable column, added without a default: instant

Revision ID: 0037
Revises: 0036
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox", sa.Column("trace", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("outbox", "trace")
