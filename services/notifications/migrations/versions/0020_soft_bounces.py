"""soft_bounces: temporary bounces, counted per address over two weeks, so repeated ones
suppress it while a single one doesn't; ck_suppressed_addresses_reason allows "soft_bounced".
The CHECK is swapped NOT VALID, so it takes the table's lock only for a moment, then validated
without blocking writes

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

NAME = "ck_suppressed_addresses_reason"
NOW = "reason IN ('bounced', 'complained', 'suppressed', 'soft_bounced')"
BEFORE = "reason IN ('bounced', 'complained', 'suppressed')"


def swap(condition: str) -> None:
    op.execute(f"ALTER TABLE suppressed_addresses DROP CONSTRAINT {NAME}")
    op.execute(
        f"ALTER TABLE suppressed_addresses ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE suppressed_addresses VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    op.create_table(
        "soft_bounces",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("address", sa.String(64), nullable=False),
        sa.Column("email_id", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("address", "email_id"),
    )
    op.create_index("ix_soft_bounces_created_at", "soft_bounces", ["created_at"])
    swap(NOW)


def downgrade() -> None:
    swap(BEFORE)
    op.drop_table("soft_bounces")
