"""The database refuses what the code never writes: a value outside its closed set (statuses,
kinds, roles), and numbers out of range (percentages, votes, counters). Each CHECK is added NOT
VALID, which takes its table's lock only for a moment, then validated in its own transaction,
which reads the rows without blocking writes

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-21
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

# (table, name, condition), as the models build them on 2026-10-21.
CHECKS = (
    ("mcp_grants", "ck_mcp_grants_scope", "scope IN ('prepza', 'prepza:read')"),
    ("messages", "ck_messages_role", "role IN ('user', 'assistant')"),
    ("messages", "ck_messages_source", "source IN ('text', 'voice')"),
    ("messages", "ck_messages_status", "status IN ('complete', 'cancelled', 'failed')"),
    ("messages", "ck_messages_vote", "vote IN (-1, 1)"),
    ("tool_calls", "ck_tool_calls_state", "state IN ('running', 'done', 'failed')"),
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
