"""an outbox: events (contact messages) saved with their change until they're published

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("data", JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("trace", sa.String(256), nullable=True),
    )
    op.create_index("ix_outbox_published_at", "outbox", ["published_at"])


def downgrade() -> None:
    op.drop_table("outbox")
