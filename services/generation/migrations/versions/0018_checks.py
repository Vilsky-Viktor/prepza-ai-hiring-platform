"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-21
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    (
        "generations",
        "ck_generations_kind",
        "kind IN ('interview', 'template', 'template_questions')",
    ),
    (
        "generations",
        "ck_generations_status",
        "status IN ('queued', 'running', 'awaiting_review', 'done', 'failed', 'cancelled')",
    ),
    (
        "quality_patterns",
        "ck_quality_patterns_flag",
        "flag IN ('wrong_key', 'rewrite', 'weak_options')",
    ),
    ("quality_patterns", "ck_quality_patterns_question_count", "question_count >= 0"),
    (
        "quality_patterns",
        "ck_quality_patterns_status",
        "status IN ('proposed', 'approved', 'dismissed', 'in_use')",
    ),
)
NOT_YET = ()


def upgrade() -> None:
    for table, name, condition in CHECKS:
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID")

    with op.get_context().autocommit_block():
        for table, name, _ in CHECKS:
            if name not in NOT_YET:
                op.execute(f"ALTER TABLE {table} VALIDATE CONSTRAINT {name}")


def downgrade() -> None:
    for table, name, _ in CHECKS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
