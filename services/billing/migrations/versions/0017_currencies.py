"""Prices in euros and pounds as well as dollars: the currency a company or a person chose, and
the one an automatic top-up's subscription started in, which Paddle charges every top-up in (the
ones running so far were all in US dollars).

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.create_table(
        "currency_choices",
        sa.Column("owner_type", sa.String(16), primary_key=True),
        sa.Column("owner_id", sa.String(128), primary_key=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.CheckConstraint(
            "currency IN ('USD', 'EUR', 'GBP')", name="ck_currency_choices_currency"
        ),
    )
    op.add_column("auto_top_ups", sa.Column("currency", sa.String(3)))
    op.execute("UPDATE auto_top_ups SET currency = 'USD' WHERE subscription_id IS NOT NULL")
    # Billing's currencies (app/constants/currencies.py); the table holds a row per wallet at
    # most, so it's validated at once.
    op.execute(
        "ALTER TABLE auto_top_ups ADD CONSTRAINT ck_auto_top_ups_currency "
        "CHECK (currency IN ('USD', 'EUR', 'GBP')) NOT VALID"
    )
    op.execute("ALTER TABLE auto_top_ups VALIDATE CONSTRAINT ck_auto_top_ups_currency")


def downgrade() -> None:
    op.drop_constraint("ck_auto_top_ups_currency", "auto_top_ups")
    op.drop_column("auto_top_ups", "currency")
    op.drop_table("currency_choices")
