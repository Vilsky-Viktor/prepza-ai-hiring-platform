"""API keys act as themselves: a note an API key writes names the key
(interview_notes.author_key_id), a nullable column without a default, instant to add

Revision ID: 0070
Revises: 0069
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0070"
down_revision = "0069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("interview_notes", sa.Column("author_key_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("interview_notes", "author_key_id")
