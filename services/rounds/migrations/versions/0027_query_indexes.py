"""The index on sessions.candidate_invite_id goes: uq_sessions_invite_topic starts with it. Built
and dropped concurrently, so writes go on meanwhile

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-21
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = ()
DROPPED = (("ix_sessions_candidate_invite_id", "sessions (candidate_invite_id)"),)


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
