"""ats_candidates(link_id, created_at): a linked job's candidates, oldest first, and the rows a
deleted job link sets to null were found by reading the whole table. Built concurrently, so
writes go on meanwhile

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-21
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

INDEX = "ix_ats_candidates_link_id_created_at"


def upgrade() -> None:
    with op.get_context().autocommit_block():
        # A build cut off earlier leaves an invalid index of this name: dropped and built again.
        op.drop_index(INDEX, "ats_candidates", if_exists=True, postgresql_concurrently=True)
        op.create_index(
            INDEX, "ats_candidates", ["link_id", "created_at"], postgresql_concurrently=True
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(INDEX, "ats_candidates", postgresql_concurrently=True)
