"""slack_connections.token_hash: each workspace token's SHA-256, so disconnecting a company finds
whether another still uses its token by an indexed lookup instead of unsealing every company's
token. Existing rows get theirs from their unsealed token (the table holds few rows); one sealed
with a key no longer set stays empty, as it matched nothing before either. The index is built
concurrently.

Revision ID: 0022
Revises: 0021
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from prepza_common.encryption import decrypt

from app.config.settings import settings
from app.helpers.slack import token_hash

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("slack_connections", sa.Column("token_hash", sa.String(64), nullable=True))
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT company_id, token FROM slack_connections")).all()
    tokens = {
        company_id: decrypt(settings.slack_encryption_key, sealed) for company_id, sealed in rows
    }
    changes = [
        {"company_id": company_id, "hash": token_hash(token)}
        for company_id, token in tokens.items()
        if token
    ]

    if changes:
        bind.execute(
            sa.text(
                "UPDATE slack_connections SET token_hash = :hash WHERE company_id = :company_id"
            ),
            changes,
        )

    with op.get_context().autocommit_block():
        op.create_index(
            "ix_slack_connections_token_hash",
            "slack_connections",
            ["token_hash"],
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    op.drop_index("ix_slack_connections_token_hash", table_name="slack_connections")
    op.drop_column("slack_connections", "token_hash")
