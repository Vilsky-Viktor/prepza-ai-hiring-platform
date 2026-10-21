"""The contract steps, now that nothing in production reads the old columns: ai_usage's float
cost_usd goes (cost, exact, is NOT NULL); company_id in ai_usage and limit_hits becomes uuid, as
in every other service; and limits' values become exact numbers, as some are amounts of USD.

Changed in place, rewriting each table once under its lock, for a reason each: an UPDATE
backfill of ai_usage is refused for the rows ck_ai_usage_service (NOT VALID) doesn't allow, and
the other tables hold a row per limit or per refusal

Revision ID: 0027
Revises: 0026
Create Date: 2026-10-22
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

# (table, column, the new type, the old one)
TYPES = (
    ("ai_usage", "company_id", "uuid", "varchar(128)"),
    ("limit_hits", "company_id", "uuid", "varchar(128)"),
    ("limit_settings", "value", "numeric(20, 6)", "double precision"),
    ("limit_changes", "old_value", "numeric(20, 6)", "double precision"),
    ("limit_changes", "new_value", "numeric(20, 6)", "double precision"),
)
FILLED = "ck_ai_usage_cost_filled"


def upgrade() -> None:
    for table, column, new, _ in TYPES:
        # migration-check: not in production; see above
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {new} USING {column}::{new}")

    op.execute("ALTER TABLE ai_usage ALTER COLUMN cost SET DEFAULT 0")
    op.execute(f"ALTER TABLE ai_usage ADD CONSTRAINT {FILLED} CHECK (cost IS NOT NULL) NOT VALID")

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE ai_usage VALIDATE CONSTRAINT {FILLED}")
        # migration-check: the validated CHECK above proves it, so this doesn't scan the table
        op.execute("ALTER TABLE ai_usage ALTER COLUMN cost SET NOT NULL")
        op.execute(f"ALTER TABLE ai_usage DROP CONSTRAINT {FILLED}")
        op.execute("ALTER TABLE ai_usage DROP COLUMN cost_usd")


def downgrade() -> None:
    op.execute("ALTER TABLE ai_usage ADD COLUMN cost_usd double precision DEFAULT 0")
    op.execute("UPDATE ai_usage SET cost_usd = cost")
    op.execute("ALTER TABLE ai_usage ALTER COLUMN cost DROP NOT NULL")
    op.execute("ALTER TABLE ai_usage ALTER COLUMN cost DROP DEFAULT")

    for table, column, _, old in TYPES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {old} USING {column}::{old}")
