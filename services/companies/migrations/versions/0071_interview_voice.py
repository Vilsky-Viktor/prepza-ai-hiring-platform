"""An interview may be taken by voice (interviews.voice): its questions are read aloud and
candidates may answer by voice. Off for every interview; a constant default, instant to add

Revision ID: 0071
Revises: 0070
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0071"
down_revision = "0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interviews", sa.Column("voice", sa.Boolean(), server_default="false", nullable=False)
    )


def downgrade() -> None:
    op.drop_column("interviews", "voice")
