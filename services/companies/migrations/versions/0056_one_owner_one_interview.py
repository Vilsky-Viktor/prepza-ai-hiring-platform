"""What the code assumes, enforced: a company has one owner (members), and a generation makes
one interview (interviews.generation_id, whose plain index this unique one replaces). Built
concurrently, so writes go on meanwhile; a build that finds duplicates fails and leaves an
invalid index, dropped when it runs again

Revision ID: 0056
Revises: 0055
Create Date: 2026-10-21
"""

from alembic import op

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None

CREATED = (
    ("uq_members_one_owner", "members (company_id) WHERE role = 'owner'"),
    ("uq_interviews_generation_id", "interviews (generation_id)"),
)
REPLACED = ("ix_interviews_generation_id", "interviews (generation_id)")


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for name, target in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE UNIQUE INDEX CONCURRENTLY {name} ON {target}")

        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {REPLACED[0]}")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {REPLACED[0]} ON {REPLACED[1]}")

        for name, _ in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
