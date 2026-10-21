"""Indexes for a template's latest addition, the generations the schedules fail or expire, those
whose text is kept, and the key checks waiting to be sent, which read whole tables. Built and
dropped concurrently, so writes go on meanwhile

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-21
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (
    (
        "ix_generations_template_additions",
        "generations (preparation_id, created_at) WHERE kind = 'template_questions'",
    ),
    (
        "ix_generations_unsettled",
        "generations (updated_at) WHERE status IN ('queued', 'running', 'awaiting_review')",
    ),
    ("ix_generations_text_kept", "generations (updated_at) WHERE text <> ''"),
    ("ix_key_checks_unsent", "key_checks (created_at) WHERE batch_id IS NULL"),
)
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
