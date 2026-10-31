"""candidate_invites hold_key: the hash migration 0036 put in older invites' keys is a plain hash
of the interview and the candidate's email, which anyone with both could match; every key's hash
is keyed (testee_common.limits.credit_keys.rekeyed, PERSON_HASH_KEY), as billing's migration 0026 does
to its copies, so the two still meet. One transaction, so a cut-off run leaves nothing half done.

Revision ID: 0057
Revises: 0056
Create Date: 2026-10-22
"""

import sqlalchemy as sa
from alembic import op
from testee_common.limits.credit_keys import rekeyed

from companies.config import settings

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, hold_key FROM candidate_invites")).all()
    changes = [{"id": id_, "key": rekeyed(key, settings.person_hash_key)} for id_, key in rows]

    if changes:
        bind.execute(
            sa.text("UPDATE candidate_invites SET hold_key = :key WHERE id = :id"), changes
        )


def downgrade() -> None:
    # A keyed hash can't be turned back; older code takes any key, so the keys stay keyed.
    pass
