"""holds and entries: candidates' keys without their email ("candidate:{interview_id}:{hash}"),
the same keys companies migration 0036 gives its invites

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-11
"""

from alembic import op
from testee_common.limits.credit_keys import ledger_key

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# "candidate:{interview_id}:{email}[:{uuid}]" becomes "candidate:{interview_id}:" and a hash of
# the old key: the same as companies' migration 0036 gives the invite.
NEW_KEY = ledger_key("key")


def upgrade() -> None:
    for table in ("holds", "entries"):
        op.execute(f"UPDATE {table} SET key = {NEW_KEY} WHERE key LIKE 'candidate:%'")


def downgrade() -> None:
    pass
