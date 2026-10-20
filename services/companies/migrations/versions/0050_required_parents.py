"""interviews.company_id, members.company_id and candidate_invites.interview_id NOT NULL, as the
models have them: the first migration made them nullable, so the database accepted a row with no
company or interview that no page could ever show

Revision ID: 0050
Revises: 0049
Create Date: 2026-10-20
"""

from alembic import op

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None

COLUMNS = [
    ("interviews", "company_id"),
    ("members", "company_id"),
    ("candidate_invites", "interview_id"),
]


def upgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(table, column, nullable=False)


def downgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(table, column, nullable=True)
