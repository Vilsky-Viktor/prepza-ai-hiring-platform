"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-21
"""

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    ("answers", "ck_answers_score", "score BETWEEN 0 AND 100"),
    ("help_votes", "ck_help_votes_vote", "vote IN (-1, 1)"),
    ("sessions", "ck_sessions_final_score", "final_score BETWEEN 0 AND 100"),
    ("sessions", "ck_sessions_question_seconds", "question_seconds > 0"),
    ("sessions", "ck_sessions_status", "status IN ('in_progress', 'finished')"),
    ("signals", "ck_signals_kind", "kind IN ('tab_leave', 'copy', 'tab_return')"),
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
