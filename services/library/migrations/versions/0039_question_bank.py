"""The shared question bank: companies' proven questions that passed the filter (bank_questions,
with their topic's embedding and no company id), the filter's verdicts (bank_checks), companies'
opt-outs per interview (interview_privacy), and a mark on a company test's copy of a bank
question (questions.bank_question_id)

Revision ID: 0039
Revises: 0038
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    op.create_table(
        "bank_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_question_id", sa.Uuid(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["source_question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_question_id"),
    )
    op.create_index("ix_bank_questions_level_language", "bank_questions", ["level", "language"])
    # Not in the ORM model: only the raw SQL in repositories/reuse.py and bank.py uses it.
    op.execute("ALTER TABLE bank_questions ADD COLUMN embedding vector(256) NOT NULL")
    op.create_table(
        "bank_checks",
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("text_hash", sa.String(length=32), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("barred", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id"),
    )
    op.create_index("ix_bank_checks_company_id", "bank_checks", ["company_id"])
    # Its company from its question, as for the questions' other tables (migration 0035).
    op.execute(
        "CREATE TRIGGER company_from_parent BEFORE INSERT ON bank_checks FOR EACH ROW "
        "EXECUTE FUNCTION company_from_parent('questions', 'question_id')"
    )
    op.create_table(
        "interview_privacy",
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("set_id", sa.Uuid(), nullable=True),
        sa.Column("generation_id", sa.Uuid(), nullable=True),
        sa.Column("keep_private", sa.Boolean(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("interview_id"),
    )
    op.create_index("ix_interview_privacy_company_id", "interview_privacy", ["company_id"])
    # A nullable column without a default: instant.
    op.add_column("questions", sa.Column("bank_question_id", sa.Uuid(), nullable=True))

    with op.get_context().autocommit_block():
        op.create_index(
            "ix_questions_bank_question_id",
            "questions",
            ["bank_question_id"],
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    op.drop_index("ix_questions_bank_question_id", table_name="questions")
    op.drop_column("questions", "bank_question_id")
    op.drop_table("interview_privacy")
    op.drop_table("bank_checks")
    op.drop_table("bank_questions")
