"""bulk_sends and bulk_recipients: one sender for legal notices and campaigns, each send's
recipients worked out once; suppressed_addresses, testee's own suppression list; campaigns and
campaign_texts. The legal notices asked for so far become bulk sends (legal_notices stays until
no running code reads it)

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

TIME = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "bulk_sends",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("about", sa.String(64), nullable=False),
        sa.Column("asked_by", sa.String(128), nullable=False),
        sa.Column("created_at", TIME, nullable=False),
        sa.Column("prepared_at", TIME),
        sa.Column("finished_at", TIME),
        sa.Column("stopped_at", TIME),
        sa.UniqueConstraint("kind", "about"),
    )
    op.create_table(
        "bulk_recipients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "send_id",
            sa.Uuid(),
            sa.ForeignKey("bulk_sends.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("reason", sa.String(200)),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("sent_at", TIME),
        sa.Column("unsubscribed_at", TIME),
        sa.Column("complained_at", TIME),
        sa.UniqueConstraint("send_id", "user_id"),
    )
    op.create_index("ix_bulk_recipients_status", "bulk_recipients", ["status", "send_id"])
    op.create_index("ix_bulk_recipients_user_id", "bulk_recipients", ["user_id"])
    op.create_index("ix_bulk_recipients_sent_at", "bulk_recipients", ["sent_at"])
    op.create_table(
        "suppressed_addresses",
        sa.Column("address", sa.String(64), primary_key=True),
        sa.Column("reason", sa.String(16), nullable=False),
        sa.Column("created_at", TIME, nullable=False),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("link", sa.String(300)),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", TIME, nullable=False),
        sa.Column("sent_at", TIME),
    )
    op.create_index("ix_campaigns_created_at", "campaigns", ["created_at"])
    op.create_table(
        "campaign_texts",
        sa.Column(
            "campaign_id",
            sa.Uuid(),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("language", sa.String(8), primary_key=True),
        sa.Column("subject", sa.String(120), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("button", sa.String(40)),
    )
    # A notice asked for and not yet sent to everyone is prepared by the next run.
    op.execute(
        "INSERT INTO bulk_sends (id, kind, about, asked_by, created_at, finished_at) "
        "SELECT gen_random_uuid(), 'legal_' || document, version, asked_by, created_at, sent_at "
        "FROM legal_notices ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("campaign_texts")
    op.drop_table("campaigns")
    op.drop_table("suppressed_addresses")
    op.drop_table("bulk_recipients")
    op.drop_table("bulk_sends")
