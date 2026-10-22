"""An interview's section needs its company (practice has none): companies sends it with every
section since 0029, and companies' one-off backfill (python -m app.services.round_companies, in
the companies service) gave it to the sections started before. Added NOT VALID, then validated

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-22
"""

from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

NAME = "ck_sessions_company_id"


def upgrade() -> None:
    op.execute(
        f"ALTER TABLE sessions ADD CONSTRAINT {NAME} "
        "CHECK (practice OR company_id IS NOT NULL) NOT VALID"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE sessions VALIDATE CONSTRAINT {NAME}")


def downgrade() -> None:
    op.execute(f"ALTER TABLE sessions DROP CONSTRAINT {NAME}")
