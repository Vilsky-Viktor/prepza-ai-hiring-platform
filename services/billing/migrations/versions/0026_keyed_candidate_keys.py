"""holds and entries: the hash in candidates' keys ("candidate:{interview_id}:{hash}") is keyed
(prepza_common.limits.credit_keys.rekeyed, PERSON_HASH_KEY), as companies' migration 0057 does to its
invites' keys, so the two still meet; the plain hash could be matched by anyone with the
interview and the candidate's email. One transaction, so a cut-off run leaves nothing half done.

Revision ID: 0026
Revises: 0025
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from prepza_common.limits.credit_keys import rekeyed

from app.config.settings import settings
from app.constants.credits import CANDIDATE_PREFIX

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    for table in ("holds", "entries"):
        # A key names one hold, and one entry (uq_entries_key).
        keys = bind.scalars(
            sa.text(f"SELECT key FROM {table} WHERE key LIKE :prefix"),
            {"prefix": f"{CANDIDATE_PREFIX}%"},
        ).all()
        changes = [
            {
                "old": key,
                "new": CANDIDATE_PREFIX
                + rekeyed(key.removeprefix(CANDIDATE_PREFIX), settings.person_hash_key),
            }
            for key in keys
        ]

        if changes:
            bind.execute(sa.text(f"UPDATE {table} SET key = :new WHERE key = :old"), changes)


def downgrade() -> None:
    # A keyed hash can't be turned back into the plain one; the rows stay keyed.
    pass
