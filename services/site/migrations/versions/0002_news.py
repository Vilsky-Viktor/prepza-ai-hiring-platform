"""news posts, and their translations into the other languages, as library had them

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("published_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_news_published_on_created_at", "news", ["published_on", "created_at"])
    op.create_table(
        "news_translations",
        sa.Column(
            "news_id",
            sa.Uuid(),
            sa.ForeignKey("news.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("language", sa.String(8), primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("news_translations")
    op.drop_table("news")
