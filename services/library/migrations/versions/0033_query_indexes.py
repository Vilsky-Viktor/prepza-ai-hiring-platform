"""Indexes for a person's votes and reports (deletion, export), revisions newest first, templates
of the same title and topics without an embedding, which read whole tables; one index the unique
constraint already covers goes. Built and dropped concurrently, so writes go on meanwhile

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-21
"""

from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (
    ("ix_question_ratings_user_id", "question_ratings (user_id)"),
    ("ix_question_reports_user_id", "question_reports (user_id)"),
    ("ix_question_revisions_replaced_at", "question_revisions (replaced_at DESC, id)"),
    ("ix_sets_template_titles", "sets (language, lower(title)) WHERE kind = 'template'"),
    ("ix_topics_without_embedding", "topics (id) WHERE embedding IS NULL"),
)
DROPPED = (("ix_question_reports_question_id", "question_reports (question_id)"),)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for name, target in CREATED:
            # A build cut off earlier leaves an invalid index of this name: built again.
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(f"CREATE INDEX CONCURRENTLY {name} ON {target}")

        for name, _ in DROPPED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _ in CREATED:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")

        for name, target in DROPPED:
            op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {target}")
