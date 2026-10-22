"""Campaigns get a third kind, important notices ("notices": a service email whatever the email
settings), and an audience: everyone, or some groups (members of companies, candidates,
learners), of companies their owners and admins only, and for a notice some companies only.
The kind CHECKs of campaigns and bulk_sends are swapped NOT VALID, as before; the new columns
have constant defaults (instant), and their CHECKs hold for every existing row.

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

CAMPAIGN_KINDS = "kind IN ('updates', 'promotions', 'notices')"
CAMPAIGN_KINDS_BEFORE = "kind IN ('updates', 'promotions')"
SEND_KINDS = (
    "kind IN ('legal_terms', 'legal_privacy', 'legal_dpa', 'updates', 'promotions', 'notices')"
)
SEND_KINDS_BEFORE = "kind IN ('legal_terms', 'legal_privacy', 'legal_dpa', 'updates', 'promotions')"
CHECKS = {
    "ck_campaigns_groups": "groups <@ ARRAY['members', 'candidates', 'learners']::varchar[]",
    "ck_campaigns_editors_only": "NOT editors_only OR 'members' = ANY (groups)",
    "ck_campaigns_company_ids": (
        "cardinality(company_ids) <= 50 AND (cardinality(company_ids) = 0"
        " OR (kind = 'notices' AND 'members' = ANY (groups)))"
    ),
}


def swap(table: str, name: str, condition: str) -> None:
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
    op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition}) NOT VALID")


def upgrade() -> None:
    swap("campaigns", "ck_campaigns_kind", CAMPAIGN_KINDS)
    swap("bulk_sends", "ck_bulk_sends_kind", SEND_KINDS)
    op.add_column(
        "campaigns",
        sa.Column("groups", ARRAY(sa.String(16)), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "campaigns",
        sa.Column("editors_only", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "campaigns",
        sa.Column("company_ids", ARRAY(sa.Uuid()), nullable=False, server_default=sa.text("'{}'")),
    )

    for name, condition in CHECKS.items():
        op.execute(
            # migration-check: campaigns holds a few rows, written by superadmins
            f"ALTER TABLE campaigns ADD CONSTRAINT {name} CHECK ({condition})"
        )


def downgrade() -> None:
    for name in CHECKS:
        op.execute(f"ALTER TABLE campaigns DROP CONSTRAINT {name}")

    op.drop_column("campaigns", "company_ids")
    op.drop_column("campaigns", "editors_only")
    op.drop_column("campaigns", "groups")
    op.execute("DELETE FROM bulk_sends WHERE kind = 'notices'")
    op.execute("DELETE FROM campaigns WHERE kind = 'notices'")
    swap("bulk_sends", "ck_bulk_sends_kind", SEND_KINDS_BEFORE)
    swap("campaigns", "ck_campaigns_kind", CAMPAIGN_KINDS_BEFORE)
