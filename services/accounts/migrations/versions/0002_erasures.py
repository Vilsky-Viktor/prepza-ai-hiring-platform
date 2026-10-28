"""erasures: accounts deleted in the backups' life (14 days), whose deletion is run again after
a restore

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "erasures",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("erased_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="erasures_pkey"),
    )
    op.create_index(op.f("ix_erasures_erased_at"), "erasures", ["erased_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_erasures_erased_at"), table_name="erasures")
    op.drop_table("erasures")
