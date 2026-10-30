"""Voice mode: a section may be taken by voice (`voice`), the question waiting is read aloud for
`question_reading_seconds` before its own time starts, and the clips read aloud are kept once for
every candidate who hears them (`voice_clips`).

Revision ID: 0034
Revises: 0033
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions", sa.Column("voice", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("sessions", sa.Column("question_reading_seconds", sa.Integer(), nullable=True))
    op.create_table(
        "voice_clips",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("audio", sa.LargeBinary(), nullable=False),
        sa.Column("seconds", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("key", name="voice_clips_key_key"),
    )
    op.create_index("ix_voice_clips_company_id", "voice_clips", ["company_id"])
    op.create_index("ix_voice_clips_used_at", "voice_clips", ["used_at"])


def downgrade() -> None:
    op.drop_table("voice_clips")
    op.drop_column("sessions", "question_reading_seconds")
    op.drop_column("sessions", "voice")
