"""Welcome gifts were kept by a plain SHA-256 of the owner's inbox ("{kind}:{hash}"), which
anyone with a list of addresses can match; each becomes its keyed hash
(testee_common.auth.person_hash.keyed with PERSON_HASH_KEY), the same one the code now makes. One row
per company owner, so few rows.

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from testee_common.auth.person_hash import keyed

from billing.config import settings

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    keys = bind.scalars(sa.text("SELECT key FROM gifts")).all()
    changes = []

    for old in keys:
        kind, _, digest = old.rpartition(":")
        changes.append({"old": old, "new": f"{kind}:{keyed(digest, settings.person_hash_key)}"})

    if changes:
        bind.execute(sa.text("UPDATE gifts SET key = :new WHERE key = :old"), changes)


def downgrade() -> None:
    # A keyed hash can't be turned back into the plain one; the rows stay keyed.
    pass
