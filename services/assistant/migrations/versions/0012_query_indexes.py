"""Indexes in the order the lists read: a user's conversations latest first and a conversation's
messages in order, replacing the single-column ones; and AI apps by age for the retention. Built
and dropped concurrently, so writes go on meanwhile

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-21
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

# (name, what it indexes): the indexes made, and those another index covers
CREATED = (
    ("ix_conversations_user_latest", "conversations (user_id, updated_at DESC, id)"),
    ("ix_messages_conversation_order", "messages (conversation_id, created_at, id)"),
    ("ix_oauth_clients_created_at", "oauth_clients (created_at)"),
)
DROPPED = (
    ("ix_conversations_user_id", "conversations (user_id)"),
    ("ix_messages_conversation_id", "messages (conversation_id)"),
)


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
