"""Candidates' opted-out and suppressed addresses were kept as a plain SHA-256, which anyone with
a list of addresses can match; each becomes its keyed hash (prepza_common.auth.person_hash.keyed with
PERSON_HASH_KEY), the same one the code now makes from the address. Both tables hold few rows.

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from prepza_common.auth.person_hash import keyed

from app.config.settings import settings

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

# (table, the column that names a row)
TABLES = (("candidate_opt_outs", "id"), ("suppressed_addresses", "address"))


def upgrade() -> None:
    bind = op.get_bind()

    for table, row_key in TABLES:
        rows = bind.execute(sa.text(f"SELECT {row_key}, address FROM {table}")).all()
        changes = [
            {"row": row, "address": keyed(address, settings.person_hash_key)}
            for row, address in rows
        ]

        if changes:
            bind.execute(
                sa.text(f"UPDATE {table} SET address = :address WHERE {row_key} = :row"), changes
            )


def downgrade() -> None:
    # A keyed hash can't be turned back into the plain one; the rows stay keyed.
    pass
