"""Drops reporters' comments from replaced questions' kept reports (question_revisions.reports):
a revision outlives the report and its reporter's account, so it keeps only reasons and times

Revision ID: 0040
Revises: 0039
Create Date: 2026-10-30
"""

from alembic import op

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    op.execute(
        """
        UPDATE question_revisions
        SET reports = (
            SELECT coalesce(jsonb_agg(report - 'comment'), '[]'::jsonb)
            FROM jsonb_array_elements(reports) AS report
        )
        WHERE jsonb_path_exists(reports, '$[*].comment')
        """
    )


def downgrade() -> None:
    # The comments are gone for good.
    pass
