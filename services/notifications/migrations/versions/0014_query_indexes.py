"""An index on the email in a notification's data: erasing a person read every notification. Built
and dropped concurrently, so writes go on meanwhile

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-21
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (("ix_notifications_email", "notifications ((data ->> 'email'))"),)
DROPPED = ()


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for name, target in CREATED:
            # A build cut off earlier leaves an invalid index of this name: built again.
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE INDEX CONCURRENTLY {name} ON {target}")

        for name, _ in DROPPED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _ in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")

        for name, target in DROPPED:
            op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {target}")
