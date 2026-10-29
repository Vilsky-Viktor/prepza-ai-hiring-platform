"""Drop help_votes: the help chat and its votes are the assistant's (its own help_votes), and
nothing in rounds reads or writes this table any more

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("help_votes")


def downgrade() -> None:
    """The table as 0031 left it, empty, for the tests that migrate down past this one."""
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
