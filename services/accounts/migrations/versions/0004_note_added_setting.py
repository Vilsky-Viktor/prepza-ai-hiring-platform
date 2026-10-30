"""The activity digest's notes: email_preferences.note_added (on, like the digest's other kinds),
and note_added joins ck_email_consents_setting (NOT VALID, then validated in its own transaction)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

NAME = "ck_email_consents_setting"
BEFORE = (
    "candidate_finished",
    "invite_undelivered",
    "ats_not_invited",
    "interview_ready",
    "reminders",
    "updates",
    "promotions",
)
NOW = (
    "candidate_finished",
    "invite_undelivered",
    "ats_not_invited",
    "interview_ready",
    "note_added",
    "reminders",
    "updates",
    "promotions",
)


def swap(values) -> None:
    listed = ", ".join(f"'{value}'" for value in values)
    op.execute(f"ALTER TABLE email_consents DROP CONSTRAINT {NAME}")
    op.execute(
        f"ALTER TABLE email_consents ADD CONSTRAINT {NAME} CHECK (setting IN ({listed})) NOT VALID"
    )


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    # A constant default: instant.
    op.add_column(
        "email_preferences",
        sa.Column("note_added", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    swap(NOW)

    with op.get_context().autocommit_block():
        op.execute(f"ALTER TABLE email_consents VALIDATE CONSTRAINT {NAME}")


def downgrade() -> None:
    op.execute("DELETE FROM email_consents WHERE setting = 'note_added'")
    swap(BEFORE)
    op.drop_column("email_preferences", "note_added")
