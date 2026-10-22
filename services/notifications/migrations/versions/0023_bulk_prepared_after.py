"""bulk_sends.prepared_after: the last audience id a send's recipients were worked out to, so a
send to every account is worked out a page at a time, each run going on where the last stopped,
instead of all at once. A nullable column without a default: instant.

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bulk_sends", sa.Column("prepared_after", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("bulk_sends", "prepared_after")
