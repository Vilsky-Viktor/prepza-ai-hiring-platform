"""Open to offers: practice users who chose to be listed on paying companies' Discover tabs, with
their name and LinkedIn profile (`open_to_offers`), and the log of every change of that choice with the
wording agreed to (`offer_consents`).

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "open_to_offers",
        sa.Column("user_id", sa.String(128), primary_key=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=False),
        sa.Column(
            "opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_open_to_offers_opened_at", "open_to_offers", ["opened_at"])
    op.create_table(
        "offer_consents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("text_version", sa.String(16), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_offer_consents_user_id", "offer_consents", ["user_id"])


def downgrade() -> None:
    op.drop_table("offer_consents")
    op.drop_table("open_to_offers")
