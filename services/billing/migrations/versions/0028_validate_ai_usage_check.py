"""ck_ai_usage_service validated: the only rows it refused were AI calls an end-to-end test once stored
as service 'e2e' (no service of testee's), deleted first in batches; nothing in production
holds such rows. Validated, no update of an old row can stall on it

Revision ID: 0028
Revises: 0027
Create Date: 2026-10-22
"""

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

TABLE = "ai_usage"
NAME = "ck_ai_usage_service"
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
