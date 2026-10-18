"""quality_patterns: recurring mistakes in flagged or replaced questions, written as general rules
by the weekly pattern job for a superadmin to approve or dismiss. No question ids or text.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-18
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quality_patterns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("flag", sa.String(32), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column(
            "first_seen", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_quality_patterns_status", "quality_patterns", ["status"])


def downgrade() -> None:
    op.drop_index("ix_quality_patterns_status", table_name="quality_patterns")
    op.drop_table("quality_patterns")
