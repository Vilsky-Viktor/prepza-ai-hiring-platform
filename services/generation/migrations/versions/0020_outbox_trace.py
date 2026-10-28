"""Each outbox event keeps the trace of the request that saved it, sent with it to Pub/Sub, so
its consumers' logs join that request's. One nullable column, added without a default: instant

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbox", sa.Column("trace", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("outbox", "trace")
