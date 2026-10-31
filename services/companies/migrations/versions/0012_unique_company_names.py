"""company names are unique across testee, ignoring case

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Names already taken more than once stay with their first company; the later ones get
    # " (2)", " (3)" and so on, so the index can be created.
    op.execute(
        """
        UPDATE companies
        SET name = companies.name || ' (' || ranked.rank || ')'
        FROM (
            SELECT id, row_number() OVER (PARTITION BY lower(name) ORDER BY created_at, id) AS rank
            FROM companies
        ) AS ranked
        WHERE companies.id = ranked.id AND ranked.rank > 1
        """
    )
    op.create_index("uq_companies_lower_name", "companies", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_companies_lower_name", table_name="companies")
