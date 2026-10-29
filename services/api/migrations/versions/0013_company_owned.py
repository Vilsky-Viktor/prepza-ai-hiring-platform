"""Keys and web hooks belong to their company and survive the member who made them: created_by
becomes a plain record, nulled when that member deletes their account, and a web hook no longer
stops when they leave (its `stopped` flag goes)

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("api_keys", "created_by", existing_type=sa.String(length=128), nullable=True)
    op.alter_column("webhooks", "created_by", existing_type=sa.String(length=128), nullable=True)
    op.drop_column("webhooks", "stopped")


def downgrade() -> None:
    op.add_column(
        "webhooks",
        sa.Column("stopped", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("DELETE FROM webhooks WHERE created_by IS NULL")
    op.execute("DELETE FROM api_keys WHERE created_by IS NULL")
    op.alter_column("webhooks", "created_by", existing_type=sa.String(length=128), nullable=False)
    op.alter_column("api_keys", "created_by", existing_type=sa.String(length=128), nullable=False)
