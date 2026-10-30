"""Voice mode: a question's clock starts as its reading aloud starts, as in click mode, so the
seconds it was read before its time started (`sessions.question_reading_seconds`) go.

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("sessions", "question_reading_seconds")


def downgrade() -> None:
    op.add_column("sessions", sa.Column("question_reading_seconds", sa.Integer(), nullable=True))
