"""question_revisions.flag: the flag a question had when it was replaced, so the weekly pattern
job in generation knows what was wrong with it. Null for owner edits of unflagged questions and
for revisions kept before this column.

Revision ID: 0029
Revises: 0028
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("question_revisions", sa.Column("flag", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("question_revisions", "flag")
