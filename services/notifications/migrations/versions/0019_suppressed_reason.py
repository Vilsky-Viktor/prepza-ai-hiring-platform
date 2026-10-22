"""ck_suppressed_addresses_reason allows "suppressed": an address Resend suppressed an email to (on
its own list after an earlier bounce or complaint) goes on prepza's list too. Swapped NOT VALID,
so it takes the table's lock only for a moment, then validated without blocking writes

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-22
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

NAME = "ck_suppressed_addresses_reason"
NOW = "reason IN ('bounced', 'complained', 'suppressed')"
BEFORE = "reason IN ('bounced', 'complained')"


def swap(condition: str) -> None:
    op.execute(f"ALTER TABLE suppressed_addresses DROP CONSTRAINT {NAME}")
    op.execute(
        f"ALTER TABLE suppressed_addresses ADD CONSTRAINT {NAME} CHECK ({condition}) NOT VALID"
    )

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE suppressed_addresses VALIDATE CONSTRAINT {NAME}")


def upgrade() -> None:
    swap(NOW)


def downgrade() -> None:
    swap(BEFORE)
