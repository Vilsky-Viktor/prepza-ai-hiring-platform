"""Empties bulk_sends.prepared_after on sends whose audience was read or that were stopped: the
cursor names the last account read, and isn't needed after

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-30
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    # migration-check: bulk_sends has one row per notice or campaign, a few rows.
    op.execute(
        "UPDATE bulk_sends SET prepared_after = NULL "
        "WHERE prepared_after IS NOT NULL "
        "AND (prepared_at IS NOT NULL OR finished_at IS NOT NULL)"
    )


def downgrade() -> None:
    # Only a cursor of finished work: nothing to bring back.
    pass
