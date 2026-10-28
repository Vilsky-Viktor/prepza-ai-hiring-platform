"""email_preferences, email_consents and terms_acceptances, as library had them

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SETTINGS = (
    "candidate_finished",
    "invite_undelivered",
    "ats_not_invited",
    "interview_ready",
    "reminders",
    "updates",
    "promotions",
)


def one_of(column: str, values) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def upgrade() -> None:
    defaults = {setting: setting not in ("updates", "promotions") for setting in SETTINGS}
    op.create_table(
        "email_preferences",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        *(
            sa.Column(
                setting,
                sa.Boolean(),
                nullable=False,
                server_default=sa.true() if on else sa.false(),
            )
            for setting, on in defaults.items()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("user_id", name="email_preferences_pkey"),
    )
    op.create_table(
        "email_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("setting", sa.String(length=32), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("basis", sa.String(length=16), nullable=False),
        sa.Column("text_version", sa.String(length=16), nullable=False),
        sa.Column("changed_by", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(one_of("setting", SETTINGS), name="ck_email_consents_setting"),
        sa.CheckConstraint(
            one_of("source", ("sign_in", "settings", "unsubscribe", "admin")),
            name="ck_email_consents_source",
        ),
        sa.CheckConstraint(
            one_of("basis", ("choice", "soft_opt_in")), name="ck_email_consents_basis"
        ),
        sa.PrimaryKeyConstraint("id", name="email_consents_pkey"),
    )
    op.create_index("ix_email_consents_user_id", "email_consents", ["user_id"])
    op.create_table(
        "terms_acceptances",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=10), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "version", name="terms_acceptances_pkey"),
    )


def downgrade() -> None:
    op.drop_table("terms_acceptances")
    op.drop_index("ix_email_consents_user_id", table_name="email_consents")
    op.drop_table("email_consents")
    op.drop_table("email_preferences")
