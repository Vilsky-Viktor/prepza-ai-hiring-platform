"""batch_work: translations, new options and rewritten questions wait here for OpenAI's Batch
API (half price) instead of calling the model at once; a new, empty table

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_work",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Text(), server_default="", nullable=False),
        sa.Column("step", sa.Text(), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default="0", nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("body", JSONB(), nullable=False),
        sa.Column("batch_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("kind", "subject_id", "key", name="uq_batch_work_kind_subject_id_key"),
        sa.CheckConstraint(
            "kind IN ('news', 'campaign', 'new_options', 'rewrite')", name="ck_batch_work_kind"
        ),
        sa.CheckConstraint(
            "step IN ('translate', 'question', 'options')", name="ck_batch_work_step"
        ),
        sa.CheckConstraint("attempt >= 0", name="ck_batch_work_attempt"),
    )
    op.create_index("ix_batch_work_batch_id", "batch_work", ["batch_id"])
    op.create_index(
        "ix_batch_work_unsent",
        "batch_work",
        ["created_at"],
        postgresql_where=sa.text("batch_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("batch_work")
