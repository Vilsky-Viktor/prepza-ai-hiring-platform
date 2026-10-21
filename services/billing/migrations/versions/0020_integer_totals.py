"""The money a top-up, refund or chargeback moved as an integer (`total_minor`, minor units)
beside the old text `total`, backfilled in batches. Money is never text: the code writes both and
reads the integer; the text column goes once no running version reads it.

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

TABLES = ("entries", "purchases")
# Rows backfilled per transaction, so no statement holds many row locks at once.
BATCH = 1000


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")

    for table in TABLES:
        op.add_column(table, sa.Column("total_minor", sa.BigInteger(), nullable=True))

    with op.get_context().autocommit_block():
        connection = op.get_bind()

        for table in TABLES:
            while True:
                moved = connection.execute(
                    sa.text(
                        f"UPDATE {table} SET total_minor = total::bigint WHERE id IN ("
                        f"SELECT id FROM {table} WHERE total_minor IS NULL "
                        f"AND total ~ '^[0-9]+$' LIMIT {BATCH})"
                    )
                ).rowcount

                if moved < BATCH:
                    break


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "total_minor")
