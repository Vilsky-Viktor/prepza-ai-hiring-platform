"""Every tenant's row carries its company: candidate_invites gets company_id from its interview,
filled in batches, indexed and NOT NULL, with a foreign key (NOT VALID, then validated) so a
company's deletion takes its invites. And a person is a member of a company once
(uq_members_company_user, built concurrently)

Revision ID: 0058
Revises: 0057
Create Date: 2026-10-22
"""

from alembic import op
from prepza_common.tenant_columns import add_company_id, drop_company_id

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None

FILL = (
    "UPDATE candidate_invites c SET company_id = i.company_id FROM interviews i "
    "WHERE i.id = c.interview_id AND c.ctid IN "
    "(SELECT ctid FROM candidate_invites WHERE company_id IS NULL LIMIT 1000)"
)
FK = "candidate_invites_company_id_fkey"


def upgrade() -> None:
    add_company_id(op, "candidate_invites", FILL)
    op.execute(
        f"ALTER TABLE candidate_invites ADD CONSTRAINT {FK} FOREIGN KEY (company_id) "
        "REFERENCES companies (id) ON DELETE CASCADE NOT VALID"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE candidate_invites VALIDATE CONSTRAINT {FK}")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS uq_members_company_user")
        op.execute(
            "CREATE UNIQUE INDEX CONCURRENTLY uq_members_company_user "
            "ON members (company_id, user_id) WHERE user_id IS NOT NULL"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS uq_members_company_user")

    drop_company_id(op, "candidate_invites")
