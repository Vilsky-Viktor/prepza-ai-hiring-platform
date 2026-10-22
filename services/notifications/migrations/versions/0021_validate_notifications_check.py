"""ck_notifications_kind validated: the only rows it refused were notifications of a kind no
longer sent (a test's 'kit_ready'), deleted first in batches. Validated, no update of an old row
can stall on it

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-22
"""

from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

TABLE = "notifications"
NAME = "ck_notifications_kind"
# The CHECK's condition, as Postgres keeps it.
CONDITION = (
    "SELECT regexp_replace(pg_get_constraintdef(oid), '^CHECK (.*) NOT VALID$', '\\1') "
    "FROM pg_constraint WHERE conname = '{name}'"
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        bind = op.get_bind()
        condition = bind.exec_driver_sql(CONDITION.format(name=NAME)).scalar()
        refused = (
            f"DELETE FROM {TABLE} WHERE ctid IN "
            f"(SELECT ctid FROM {TABLE} WHERE NOT {condition} LIMIT 1000)"
        )

        # A batch at a time, each its own transaction, until none is left.
        while bind.exec_driver_sql(refused).rowcount:
            pass

        op.execute(f"ALTER TABLE {TABLE} VALIDATE CONSTRAINT {NAME}")


def downgrade() -> None:
    # A validated CHECK stays one; the deleted rows were a test's leftovers.
    pass
