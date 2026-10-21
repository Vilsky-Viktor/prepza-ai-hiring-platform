"""Prices in Canadian and Australian dollars, shekels, zlotys, yen, won, New Taiwan and Hong Kong
dollars, Swiss francs, baht, Singapore dollars and rupees too: the currency checks allow them.

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-21
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

TABLES = ("auto_top_ups", "currency_choices")
NOW = (
    "('USD', 'EUR', 'GBP', 'CAD', 'AUD', 'ILS', 'PLN', 'JPY', 'KRW', 'TWD', 'HKD', 'CHF', 'THB', "
    "'SGD', 'INR')"
)
BEFORE = "('USD', 'EUR', 'GBP')"


def checks(allowed: str) -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")

    for table in TABLES:
        name = f"ck_{table}_currency"
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
        # Small tables (a row per wallet or owner at most): validated at once.
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK (currency IN {allowed})")


def upgrade() -> None:
    checks(NOW)


def downgrade() -> None:
    checks(BEFORE)
