"""An automatic top-up keeps the price each charge was agreed at, so a new price list applies
only after its notice: the agreed price and its currency, the next price and the day from which
charges cost it.

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

PRICES = ("price", "next_price")
CURRENCIES = (
    "('USD', 'EUR', 'GBP', 'CAD', 'AUD', 'ILS', 'PLN', 'JPY', 'KRW', 'TWD', 'HKD', 'CHF', 'THB', "
    "'SGD', 'INR')"
)


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")

    for column in PRICES:
        op.add_column("auto_top_ups", sa.Column(column, sa.BigInteger(), nullable=True))

    op.add_column(
        "auto_top_ups", sa.Column("next_price_from", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("auto_top_ups", sa.Column("price_currency", sa.String(3), nullable=True))
    # The new column is empty, and the table holds a row per company with automatic top-up.
    # migration-check: a few rows, all with an empty column, so validating takes no time
    op.create_check_constraint(
        "ck_auto_top_ups_price_currency", "auto_top_ups", f"price_currency IN {CURRENCIES}"
    )


def downgrade() -> None:
    op.drop_constraint("ck_auto_top_ups_price_currency", "auto_top_ups")

    for column in ("price_currency", "next_price_from", *PRICES):
        op.drop_column("auto_top_ups", column)
