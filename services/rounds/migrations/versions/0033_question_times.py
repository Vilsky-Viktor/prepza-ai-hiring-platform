"""Each question of a section carries its own time (`seconds` in `questions`), which its deadline
counts from; sections drawn before it get the section's time per question on every question, as
they had. Filled in batches.

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None

FILL = sa.text(
    """
    UPDATE sessions s SET questions = (
        SELECT jsonb_agg(q || jsonb_build_object('seconds', s.question_seconds) ORDER BY n)
        FROM jsonb_array_elements(s.questions) WITH ORDINALITY AS t(q, n)
    )
    WHERE s.id IN (
        SELECT id FROM sessions
        WHERE question_seconds IS NOT NULL
            AND jsonb_array_length(questions) > 0
            AND NOT questions -> 0 ? 'seconds'
        LIMIT 1000
    )
    """
)


def upgrade() -> None:
    connection = op.get_bind()

    while connection.execute(FILL).rowcount:
        pass


def downgrade() -> None:
    """Nothing: older code reads no `seconds` and leaves it in place."""
