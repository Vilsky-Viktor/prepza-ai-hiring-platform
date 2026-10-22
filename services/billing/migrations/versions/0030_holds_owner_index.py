"""holds(owner_type, owner_id): a deleted company's holds go a batch at a time, and each batch
found them by reading the whole table. Built concurrently, so writes go on meanwhile

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-22
"""

from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

INDEX = "ix_holds_owner"


def upgrade() -> None:
    with op.get_context().autocommit_block():
        # A build cut off earlier leaves an invalid index of this name: dropped and built again.
        op.drop_index(INDEX, "holds", if_exists=True, postgresql_concurrently=True)
        op.create_index(INDEX, "holds", ["owner_type", "owner_id"], postgresql_concurrently=True)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(INDEX, "holds", postgresql_concurrently=True)
