"""removed_invites: candidates companies erased in the backups' life (14 days), erased again
after a restore

Revision ID: 0059
Revises: 0058
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "removed_invites",
        sa.Column("invite_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("invite_id", name="removed_invites_pkey"),
    )
    op.create_index("ix_removed_invites_removed_at", "removed_invites", ["removed_at"])


def downgrade() -> None:
    op.drop_index("ix_removed_invites_removed_at", table_name="removed_invites")
    op.drop_table("removed_invites")
