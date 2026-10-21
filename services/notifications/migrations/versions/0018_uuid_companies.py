"""Company and invite ids as uuid, as in every other service: slack_connections.company_id and
candidate_opt_outs.company_id and invite_id. Changed in place, rewriting each table once: not in
production, and each holds a row per company or per opt-out

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-22
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

# (table, column, its type before)
COLUMNS = (
    ("slack_connections", "company_id", "varchar(128)"),
    ("candidate_opt_outs", "company_id", "varchar(128)"),
    ("candidate_opt_outs", "invite_id", "varchar(64)"),
)


def upgrade() -> None:
    for table, column, _ in COLUMNS:
        # migration-check: not in production; see above
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE uuid USING {column}::uuid")


def downgrade() -> None:
    for table, column, old in COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {old} USING {column}::text")
