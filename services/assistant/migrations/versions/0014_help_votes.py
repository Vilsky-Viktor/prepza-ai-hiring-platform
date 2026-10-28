"""help_votes: thumbs up or down on the help chat's answers, moved here from rounds with the help
chat, by the answer's id, with its Langfuse trace (null when Langfuse wasn't set up). No text and
no voter

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "help_votes",
        sa.Column("answer_id", sa.Uuid(), primary_key=True),
        sa.Column("trace_id", sa.String(32), nullable=True),
        sa.Column("vote", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("vote IN (-1, 1)", name="ck_help_votes_vote"),
    )


def downgrade() -> None:
    op.drop_table("help_votes")
